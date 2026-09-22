// Tutor tools: instructor/courses/ (CRUD, publish, notify, learners), lectures, learners
// grouped by course and the block list. All routes here require user_cat === 'instructor'.
import { api, rows } from '../api.js';
import { navigate, link, seg } from '../router.js';
import {
  html, mount, fresh, field, onSubmit, onAction, toast, spinner, empty, errorBox, courseGrid,
  pager, avatar, fullName, profileLink, fmtDate, fileName, plural, setTitle,
} from '../ui.js';

const draftValue = (fd, name = 'IsDraft') => (fd.get(name) ? 'true' : 'false');

// ----------------------------------------------------------------------------- my courses
export async function teach({ el, query }) {
  setTitle('Teaching');
  const page = Number(query.page) || 1;
  mount(el, html`<section>
    <div class="row between">
      <h1>My courses</h1>
      <div class="row">
        <a class="btn ghost" href="${link('/teach/learners')}">Learners</a>
        <a class="btn ghost" href="${link('/teach/blocks')}">Blocked</a>
        <a class="btn primary" href="${link('/teach/courses/new')}">+ New course</a>
      </div>
    </div>
    <div id="list">${spinner()}</div>
  </section>`);
  const list = el.querySelector('#list');
  try {
    const data = await api.get('instructor/courses/', { page });
    const courses = rows(data);
    mount(list, html`
      ${courses.length ? html`<div class="grid">${courses.map((c) => html`
        <div class="card course manage">
          <a href="${link(`/teach/courses/${c.id}`)}">
            <div class="cover">${c.COVER_PHOTO ? html`<img src="${c.COVER_PHOTO}" alt="">` : ''}
              ${c.IsDraft ? html`<span class="badge draft">Draft</span>` : ''}</div>
          </a>
          <div class="card-body">
            <h3><a href="${link(`/teach/courses/${c.id}`)}">${c.COURSE_NAME}</a></h3>
            <p class="meta muted">${plural(c.lecture_count, 'lecture')} · ${c.enrolled_count} enrolled · ${fmtDate(c.PUBLICATION_DATE)}</p>
            <div class="row">
              <a class="btn small" href="${link(`/teach/courses/${c.id}`)}">Manage</a>
              <a class="btn small ghost" href="${link(`/courses/${c.id}`)}">View</a>
            </div>
          </div>
        </div>`)}</div>`
        : html`<p class="empty">No courses yet. <a href="${link('/teach/courses/new')}">Create your first one</a>.</p>`}
      ${pager(data, page)}`);
    onAction(list, { page: ({ page: p }) => navigate(link('/teach', { page: p }).slice(1)) });
  } catch (err) {
    mount(list, errorBox(err));
  }
}

export function newCourse({ el }) {
  setTitle('New course');
  mount(el, html`<section class="narrow">
    <h1>New course</h1>
    <form id="new" class="card form" enctype="multipart/form-data">
      ${field({ label: 'Course name', name: 'COURSE_NAME', required: true, max: 500 })}
      ${field({ label: 'Cover photo', name: 'COVER_PHOTO', type: 'file', accept: 'image/*', required: true })}
      <div class="field check"><label><input type="checkbox" name="IsDraft" checked> Save as draft (hidden from learners until published)</label>
        <small class="field-error" data-error-for="IsDraft"></small></div>
      <p class="form-error"></p>
      <button class="btn primary" type="submit">Create course</button>
    </form>
  </section>`);
  onSubmit(el.querySelector('#new'), async (fd) => {
    fd.set('IsDraft', draftValue(fd));
    const c = await api.post('instructor/courses/', fd);
    toast(`Created "${c.COURSE_NAME}".`, 'success');
    navigate(`/teach/courses/${c.id}`, { replace: true });
  });
}

// ----------------------------------------------------------------------------- one course
export async function manageCourse({ el, params, user }) {
  const id = params.id;
  const base = `instructor/courses/${id}/`;
  let c;

  async function load() {
    c = await api.get(base);
    setTitle(`Manage · ${c.COURSE_NAME}`);
  }
  try { await load(); } catch (err) { mount(el, errorBox(err)); return; }

  mount(el, html`<section class="manage-page">
    <p class="crumbs"><a href="${link('/teach')}">My courses</a> › <span id="crumb"></span></p>
    <div class="cols">
      <div class="main">
        <section id="lectures"></section>
        <section id="learners"></section>
      </div>
      <aside id="side"></aside>
    </div>
  </section>`);

  let side = el.querySelector('#side');
  let lecturesBox = el.querySelector('#lectures');
  let learnersBox = el.querySelector('#learners');

  function renderSide() {
    side = fresh(side);
    el.querySelector('#crumb').textContent = c.COURSE_NAME;
    mount(side, html`
      <div class="card pad">
        <div class="cover">${c.COVER_PHOTO ? html`<img src="${c.COVER_PHOTO}" alt="">` : ''}
          ${c.IsDraft ? html`<span class="badge draft">Draft</span>` : html`<span class="badge ok">Published</span>`}</div>
        <h2>${c.COURSE_NAME}</h2>
        <p class="muted small">${c.enrolled_count} enrolled · ${plural(c.lecture_count, 'lecture')} · created ${fmtDate(c.PUBLICATION_DATE)}</p>
        <div class="row">
          <a class="btn ghost small" href="${link(`/courses/${id}`)}">View as learner</a>
          ${c.IsDraft ? html`<button class="btn primary small" data-action="publish">Publish</button>` : ''}
        </div>
      </div>

      <form id="edit" class="card form" enctype="multipart/form-data">
        <h3>Edit</h3>
        ${field({ label: 'Course name', name: 'COURSE_NAME', value: c.COURSE_NAME, required: true, max: 500 })}
        ${field({ label: 'Replace cover', name: 'COVER_PHOTO', type: 'file', accept: 'image/*' })}
        <div class="field check"><label><input type="checkbox" name="IsDraft" ${c.IsDraft ? 'checked' : ''}> Draft</label></div>
        <p class="form-error"></p>
        <button class="btn primary" type="submit">Save</button>
      </form>

      <form id="notify" class="card form">
        <h3>Email all learners</h3>
        ${field({ label: 'Message', name: 'message', type: 'textarea', rows: 3, required: true, max: 1000 })}
        <p class="form-error"></p>
        <button class="btn" type="submit">Send to ${plural(c.enrolled_count, 'learner')}</button>
      </form>

      <div class="card pad danger-zone">
        <h3>Delete course</h3>
        <p class="muted small">Removes the course, its lectures and every enrolment.</p>
        <button class="btn danger" data-action="delete">Delete course</button>
      </div>`);

    onSubmit(side.querySelector('#edit'), async (fd) => {
      fd.set('IsDraft', draftValue(fd));
      await api.patch(base, fd);
      toast('Course saved.', 'success');
      await refresh();
    });
    onSubmit(side.querySelector('#notify'), async (fd, form) => {
      const data = await api.post(base + 'notify/', { message: fd.get('message') });
      toast(data.detail, 'success');
      form.reset();
    });
    onAction(side, {
      publish: async () => {
        await api.post(base + 'publish/');
        toast('Course published.', 'success');
        await refresh();
      },
      delete: async () => {
        if (!confirm(`Delete "${c.COURSE_NAME}" and all of its lectures?`)) return;
        await api.del(base);
        toast('Course deleted.');
        navigate('/teach', { replace: true });
      },
    });
  }

  function renderLectures() {
    lecturesBox = fresh(lecturesBox);
    const lectures = c.lectures || [];
    mount(lecturesBox, html`<h2>Lectures <span class="muted">(${lectures.length})</span></h2>
      ${lectures.length ? html`<ol class="lecture-list manage">${lectures.map((l, i) => html`
        <li id="lec-${l.id}">
          <div class="row between">
            <span><strong>${i + 1}. ${l.NAME}</strong>
              ${l.VIDEO ? html` <a class="small" href="${l.VIDEO}" target="_blank" rel="noopener">video</a>` : html` <span class="muted small">no video</span>`}
              ${l.ADDITIONAL_FILES ? html` · <a class="small" href="${l.ADDITIONAL_FILES}" download>${fileName(l.ADDITIONAL_FILES)}</a>` : ''}
            </span>
            <span class="row">
              <button class="btn small ghost" data-action="edit" data-id="${l.id}">Edit</button>
              <button class="btn small ghost danger" data-action="remove" data-id="${l.id}" data-name="${l.NAME}">Delete</button>
            </span>
          </div>
          <div class="editor"></div>
        </li>`)}</ol>` : empty('No lectures yet. Add the first one below.')}

      <form id="add-lecture" class="card form" enctype="multipart/form-data">
        <h3>Add a lecture</h3>
        ${field({ label: 'Title', name: 'NAME', required: true, max: 500 })}
        <div class="two">
          ${field({ label: 'Video', name: 'VIDEO', type: 'file', accept: '.mp4,.mkv,.mp3', hint: 'mp4, mkv or mp3' })}
          ${field({ label: 'Extra files', name: 'ADDITIONAL_FILES', type: 'file', accept: '.zip,.rar', hint: 'zip or rar, optional' })}
        </div>
        <p class="form-error"></p>
        <button class="btn primary" type="submit">Upload lecture</button>
      </form>`);

    onSubmit(lecturesBox.querySelector('#add-lecture'), async (fd) => {
      await api.post(base + 'lectures/', fd);
      toast('Lecture added.', 'success');
      await refresh();
    });

    onAction(lecturesBox, {
      edit: ({ id: lid }) => {
        const l = lectures.find((x) => String(x.id) === lid);
        const box = lecturesBox.querySelector(`#lec-${lid} .editor`);
        if (box.querySelector('form')) { box.innerHTML = ''; return; }
        mount(box, html`<form class="form inline-edit" enctype="multipart/form-data">
          ${field({ label: 'Title', name: 'NAME', value: l.NAME, required: true, max: 500 })}
          <div class="two">
            ${field({ label: 'Replace video', name: 'VIDEO', type: 'file', accept: '.mp4,.mkv,.mp3' })}
            ${field({ label: 'Replace files', name: 'ADDITIONAL_FILES', type: 'file', accept: '.zip,.rar' })}
          </div>
          <p class="form-error"></p>
          <div class="row"><button class="btn primary small" type="submit">Save</button>
            <button class="btn ghost small" type="button" data-action="edit" data-id="${lid}">Cancel</button></div>
        </form>`);
        onSubmit(box.querySelector('form'), async (fd) => {
          await api.patch(`${base}lectures/${lid}/`, fd);
          toast('Lecture saved.', 'success');
          await refresh();
        });
      },
      remove: async ({ id: lid, name }) => {
        if (!confirm(`Delete lecture "${name}"?`)) return;
        await api.del(`${base}lectures/${lid}/`);
        toast('Lecture deleted.');
        await refresh();
      },
    });
  }

  async function renderLearners() {
    learnersBox = fresh(learnersBox);
    mount(learnersBox, html`<h2>Learners</h2>${spinner()}`);
    try {
      const learners = await api.get(base + 'learners/');
      mount(learnersBox, html`<h2>Learners <span class="muted">(${learners.length})</span></h2>
        ${learners.length ? html`<ul class="people">${learners.map((s) => learnerRow(s, user))}</ul>`
          : empty('Nobody has enrolled yet.')}`);
      onAction(learnersBox, {
        block: async ({ username }) => {
          if (!confirm(`Block ${username} from all your courses?`)) return;
          await api.post('instructor/blocks/', { USER_NAME: username });
          toast(`${username} blocked.`);
          await renderLearners();
        },
      });
    } catch (err) {
      mount(learnersBox, html`<h2>Learners</h2>${errorBox(err)}`);
    }
  }

  async function refresh() {
    await load();
    renderSide();
    renderLectures();
  }

  renderSide();
  renderLectures();
  await renderLearners();
}

function learnerRow(s, me) {
  return html`<li class="person">
    ${avatar(s, 'sm')}
    <a href="${profileLink(s)}"><strong>${fullName(s)}</strong> <span class="muted">@${s.USER_NAME}</span></a>
    <span class="row">
      <a class="btn small ghost" href="${link(`/messages/${seg(me.USER_NAME)}/${seg(s.USER_NAME)}`)}">Message</a>
      <button class="btn small ghost danger" data-action="block" data-username="${s.USER_NAME}">Block</button>
    </span>
  </li>`;
}

// ----------------------------------------------------------------------------- learners
export async function learners({ el, user }) {
  setTitle('Learners');
  mount(el, html`<section><h1>Learners by course</h1><div id="list">${spinner()}</div></section>`);

  let list = el.querySelector('#list');
  async function render() {
    list = fresh(list);
    try {
      const groups = await api.get('instructor/learners/');
      mount(list, groups.length ? groups.map((g) => html`
        <div class="card pad">
          <h3><a href="${link(`/teach/courses/${g.course.id}`)}">${g.course.COURSE_NAME}</a>
            ${g.course.IsDraft ? html`<span class="badge draft">Draft</span>` : ''}
            <span class="muted">· ${plural(g.learners.length, 'learner')}</span></h3>
          ${g.learners.length ? html`<ul class="people">${g.learners.map((s) => learnerRow(s, user))}</ul>` : empty('No learners yet.')}
        </div>`) : empty('You have no courses yet.'));
      onAction(list, {
        block: async ({ username }) => {
          if (!confirm(`Block ${username} from all your courses?`)) return;
          await api.post('instructor/blocks/', { USER_NAME: username });
          toast(`${username} blocked.`);
          // a block hides the learner from every one of this tutor's courses
          await render();
        },
      });
    } catch (err) {
      mount(list, errorBox(err));
    }
  }
  await render();
}

// ----------------------------------------------------------------------------- blocks
export async function blocks({ el }) {
  setTitle('Blocked learners');
  mount(el, html`<section class="narrow">
    <h1>Blocked learners</h1>
    <form id="block" class="card form">
      ${field({ label: 'Block a learner by username', name: 'USER_NAME', required: true, max: 50 })}
      <p class="form-error"></p>
      <button class="btn danger" type="submit">Block</button>
    </form>
    <div id="list">${spinner()}</div>
  </section>`);

  let list = el.querySelector('#list');
  async function renderList() {
    list = fresh(list);
    try {
      const blocked = await api.get('instructor/blocks/');
      mount(list, blocked.length ? html`<ul class="people card pad">${blocked.map((s) => html`
        <li class="person">
          ${avatar(s, 'sm')}
          <a href="${profileLink(s)}"><strong>${fullName(s)}</strong> <span class="muted">@${s.USER_NAME}</span></a>
          <button class="btn small ghost" data-action="unblock" data-username="${s.USER_NAME}">Unblock</button>
        </li>`)}</ul>` : empty('Nobody is blocked.'));
      onAction(list, {
        unblock: async ({ username }) => {
          await api.del(`instructor/blocks/${seg(username)}/`);
          toast(`${username} unblocked.`);
          await renderList();
        },
      });
    } catch (err) {
      mount(list, errorBox(err));
    }
  }

  onSubmit(el.querySelector('#block'), async (fd, form) => {
    const s = await api.post('instructor/blocks/', { USER_NAME: fd.get('USER_NAME').trim() });
    toast(`${s.USER_NAME} blocked.`);
    form.reset();
    await renderList();
  });
  await renderList();
}
