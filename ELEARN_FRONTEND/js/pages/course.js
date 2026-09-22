// One course: detail with viewer flags, lectures (media only when `can_watch`), reviews and
// the learner's own actions (enrol / drop / rate / review / appeal / message the tutor).
import { api, rows, ApiError } from '../api.js';
import { link, seg } from '../router.js';
import {
  html, mount, fresh, spinner, empty, errorBox, toast, onAction, onSubmit, avatar, fullName,
  profileLink, ratingLine, fmtDate, fileName, pager, plural, setTitle,
} from '../ui.js';

export async function course({ el, params, user }) {
  const id = params.id;
  let c;

  async function load() {
    c = await api.get(`courses/${id}/`);
    setTitle(c.COURSE_NAME);
  }

  try { await load(); } catch (err) { mount(el, errorBox(err)); return; }

  mount(el, html`<article class="course-page">
    <header id="head"></header>
    <div class="cols">
      <div class="main">
        <section id="lectures"></section>
        <section id="reviews"></section>
      </div>
      <aside id="side"></aside>
    </div>
  </article>`);

  const head = el.querySelector('#head');
  // these three get delegated listeners, so each render starts from a fresh node
  let side = el.querySelector('#side');
  let lecturesBox = el.querySelector('#lectures');
  let reviewsBox = el.querySelector('#reviews');

  function renderHead() {
    const r = c.rating || { average: 0, count: 0, breakdown: {} };
    mount(head, html`
      <div class="cover big">${c.COVER_PHOTO ? html`<img src="${c.COVER_PHOTO}" alt="">` : ''}</div>
      <div class="head-body">
        <h1>${c.COURSE_NAME} ${c.IsDraft ? html`<span class="badge draft">Draft</span>` : ''}</h1>
        <p class="muted">by <a href="${profileLink(c.instructor)}">${fullName(c.instructor)}</a>
          · published ${fmtDate(c.PUBLICATION_DATE)} · ${plural(c.lecture_count, 'lecture')} · ${c.enrolled_count} enrolled</p>
        <div class="rating-summary">
          <div>${ratingLine(r)}</div>
          <div class="bars">${[5, 4, 3, 2, 1].map((n) => {
            const count = (r.breakdown && r.breakdown[String(n)]) || 0;
            const pct = r.count ? Math.round((count / r.count) * 100) : 0;
            return html`<div class="bar"><span>${n}★</span><i><b style="width:${pct}%"></b></i><span class="muted">${count}</span></div>`;
          })}</div>
        </div>
      </div>`);
  }

  function renderLectures() {
    lecturesBox = fresh(lecturesBox);
    const lectures = c.lectures || [];
    const can = c.viewer && c.viewer.can_watch;
    mount(lecturesBox, html`<h2>Lectures</h2>
      ${!lectures.length ? empty('No lectures uploaded yet.') : html`
        ${can ? html`<div id="player" class="player"><p class="muted">Pick a lecture to start watching.</p></div>` :
          html`<p class="notice">${c.viewer && c.viewer.blocked ? 'The tutor has blocked you from this course.' :
            user ? 'Enrol to watch the lectures.' : html`<a href="${link('/login', { next: `/courses/${id}` })}">Log in</a> and enrol to watch the lectures.`}</p>`}
        <ol class="lecture-list">${lectures.map((l, i) => html`
          <li>
            ${can ? html`<button class="linklike" data-action="play" data-index="${i}">${i + 1}. ${l.NAME}</button>`
                  : html`<span>${i + 1}. ${l.NAME}</span> <span class="muted">🔒</span>`}
            ${can && l.ADDITIONAL_FILES ? html` <a class="muted small" href="${l.ADDITIONAL_FILES}" download>files: ${fileName(l.ADDITIONAL_FILES)}</a>` : ''}
          </li>`)}
        </ol>`}`);

    onAction(lecturesBox, {
      play: ({ index }) => {
        const l = lectures[Number(index)];
        mount(lecturesBox.querySelector('#player'), l.VIDEO
          ? html`<h3>${l.NAME}</h3><video controls preload="metadata" src="${l.VIDEO}"></video>`
          : html`<h3>${l.NAME}</h3><p class="muted">This lecture has no video.</p>`);
        lecturesBox.querySelectorAll('.lecture-list li').forEach((li, i) => li.classList.toggle('active', i === Number(index)));
      },
    });
  }

  async function renderReviews(page = 1) {
    reviewsBox = fresh(reviewsBox);
    mount(reviewsBox, html`<h2>Reviews</h2>${spinner()}`);
    try {
      const data = await api.get(`courses/${id}/reviews/`, { page });
      const list = rows(data);
      mount(reviewsBox, html`<h2>Reviews <span class="muted">(${data.count ?? list.length})</span></h2>
        ${!list.length ? empty('No reviews yet.') : list.map((rv) => html`
          <div class="review">
            ${avatar(rv.USER_NAME, 'sm')}
            <div>
              <p><a href="${profileLink(rv.USER_NAME)}"><strong>${fullName(rv.USER_NAME)}</strong></a>
                 <span class="muted small">${fmtDate(rv.WRITING_DATE)}</span></p>
              <p>${rv.OPINION}</p>
            </div>
          </div>`)}
        ${pager(data, page)}`);
      onAction(reviewsBox, { page: ({ page: p }) => renderReviews(Number(p)) });
    } catch (err) {
      mount(reviewsBox, html`<h2>Reviews</h2>${errorBox(err)}`);
    }
  }

  // ------------------------------------------------------------------ learner side panel
  async function renderSide() {
    side = fresh(side);
    const v = c.viewer || {};
    if (!user) {
      mount(side, html`<div class="card pad">
        <p>Log in as a learner to enrol in this course.</p>
        <a class="btn primary block" href="${link('/login', { next: `/courses/${id}` })}">Log in</a>
        <a class="btn ghost block" href="${link('/register')}">Create an account</a>
      </div>`);
      return;
    }
    if (v.user_cat === 'instructor') {
      mount(side, v.is_owner
        ? html`<div class="card pad"><p>This is your course.</p>
            <a class="btn primary block" href="${link(`/teach/courses/${id}`)}">Manage course</a></div>`
        : html`<div class="card pad muted">Tutors can browse courses but only learners enrol.</div>`);
      return;
    }

    if (v.blocked) {
      mount(side, html`<div class="card pad">
        <p class="notice error">This tutor has blocked you. You can send them an appeal.</p>
        <form id="appeal" class="form">
          <div class="field"><label for="f-appeal">Your message</label>
            <textarea id="f-appeal" name="appeal" rows="4" required maxlength="2000"></textarea>
            <small class="field-error" data-error-for="appeal"></small></div>
          <p class="form-error"></p>
          <button class="btn primary block" type="submit">Send appeal</button>
        </form></div>`);
      onSubmit(side.querySelector('#appeal'), async (fd, form) => {
        const data = await api.post(`student/courses/${id}/appeal/`, { appeal: fd.get('appeal') });
        toast(data.detail, data.email_sent ? 'success' : 'error');
        form.reset();
      });
      return;
    }

    if (!v.enrolled) {
      mount(side, html`<div class="card pad">
        <p>Enrol to watch the lectures, rate the course and chat with the tutor.</p>
        <button class="btn primary block" data-action="enroll">Enrol now</button>
      </div>`);
      onAction(side, {
        enroll: async () => {
          const data = await api.post(`student/courses/${id}/enroll/`);
          toast(data.detail, 'success');
          await refresh();
        },
      });
      return;
    }

    // enrolled learner: rating, review, tutor chat, drop
    let myRating = null;
    let myReview = null;
    try { myRating = await api.get(`student/courses/${id}/rating/`); } catch (e) { if (!(e instanceof ApiError && e.status === 404)) throw e; }
    try { myReview = await api.get(`student/courses/${id}/review/`); } catch (e) { if (!(e instanceof ApiError && e.status === 404)) throw e; }

    mount(side, html`<div class="card pad">
      <p class="badge ok">Enrolled</p>
      <a class="btn primary block" href="${link(`/messages/${seg(c.instructor.USER_NAME)}/${seg(user.USER_NAME)}`)}">💬 Message the tutor</a>

      <h3>Your rating</h3>
      <div class="rate" id="rate">${[1, 2, 3, 4, 5].map((n) => html`
        <button class="star ${myRating && n <= myRating.RATING ? 'on' : ''}" data-action="rate" data-n="${n}" aria-label="${n} stars">★</button>`)}
        ${myRating ? html`<button class="linklike small" data-action="unrate">clear</button>` : ''}
      </div>

      <h3>Your review</h3>
      <form id="review" class="form">
        <div class="field"><textarea name="OPINION" rows="4" required placeholder="What did you think?">${myReview ? myReview.OPINION : ''}</textarea>
          <small class="field-error" data-error-for="OPINION"></small></div>
        <p class="form-error"></p>
        <div class="row">
          <button class="btn primary" type="submit">${myReview ? 'Update review' : 'Post review'}</button>
          ${myReview ? html`<button class="btn ghost" type="button" data-action="delreview">Delete</button>` : ''}
        </div>
      </form>

      <hr>
      <button class="btn danger ghost block" data-action="drop">Drop this course</button>
    </div>`);

    onSubmit(side.querySelector('#review'), async (fd) => {
      await api.put(`student/courses/${id}/review/`, { OPINION: fd.get('OPINION') });
      toast('Review saved.', 'success');
      await refresh();
    });

    onAction(side, {
      rate: async ({ n }) => {
        await api.put(`student/courses/${id}/rating/`, { RATING: Number(n) });
        toast(`Rated ${n} star${n === '1' ? '' : 's'}.`, 'success');
        await refresh();
      },
      unrate: async () => {
        await api.del(`student/courses/${id}/rating/`);
        await refresh();
      },
      delreview: async () => {
        if (!confirm('Delete your review?')) return;
        await api.del(`student/courses/${id}/review/`);
        toast('Review deleted.');
        await refresh();
      },
      drop: async () => {
        if (!confirm(`Drop "${c.COURSE_NAME}"? You can enrol again later.`)) return;
        await api.del(`student/courses/${id}/enroll/`);
        toast('Course dropped.');
        await refresh();
      },
    });
  }

  async function refresh() {
    await load();
    renderHead();
    renderLectures();
    await Promise.all([renderReviews(), renderSide()]);
  }

  renderHead();
  renderLectures();
  await Promise.all([renderReviews(), renderSide()]);
}
