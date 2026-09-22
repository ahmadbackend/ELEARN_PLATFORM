// Public catalogue: GET courses/?search=&page=
import { api, rows } from '../api.js';
import { navigate, link } from '../router.js';
import { html, mount, courseGrid, pager, spinner, errorBox, onAction, setTitle } from '../ui.js';

export async function home({ el, query }) {
  setTitle('Courses');
  const page = Number(query.page) || 1;
  const search = query.search || '';

  mount(el, html`<section>
    <div class="hero">
      <h1>Learn something new today</h1>
      <p class="muted">Browse published courses, enrol, watch lectures and message your tutor directly.</p>
      <form id="search" class="searchbar" role="search">
        <input type="search" name="search" value="${search}" placeholder="Search courses or tutors">
        <button class="btn primary" type="submit">Search</button>
      </form>
    </div>
    <div id="list">${spinner()}</div>
  </section>`);

  el.querySelector('#search').addEventListener('submit', (e) => {
    e.preventDefault();
    navigate(link('/', { search: e.target.search.value.trim() }).slice(1));
  });

  const list = el.querySelector('#list');
  try {
    const data = await api.get('courses/', { search, page });
    mount(list, html`
      ${search ? html`<p class="muted">Results for “${search}” · <a href="${link('/')}">clear</a></p>` : ''}
      ${courseGrid(rows(data))}
      ${pager(data, page)}`);
    onAction(list, {
      page: ({ page: p }) => navigate(link('/', { search, page: p }).slice(1)),
    });
  } catch (err) {
    mount(list, errorBox(err));
  }
}
