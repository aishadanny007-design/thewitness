const entryArticle = document.querySelector('#entry');
const archiveList = document.querySelector('[data-archive-list]');
const latestDate = document.querySelector('[data-latest-date]');
const latestSummary = document.querySelector('[data-latest-summary]');

function setStatus(message) {
  if (!entryArticle) return;
  entryArticle.innerHTML = `
    <header class="entry-header">
      <p class="entry-kicker">Loading</p>
      <h2 id="entry-title">${message}</h2>
    </header>
  `;
}

function renderEntry(entry) {
  if (!entryArticle) return;
  entryArticle.innerHTML = entry.html;
  const bodyStart = entryArticle.querySelector('.entry-header');
  const sections = [...entryArticle.querySelectorAll('section')];
  if (bodyStart && sections.length) {
    const body = document.createElement('div');
    body.className = 'entry-body';
    sections[0].before(body);
    sections.forEach((section) => body.appendChild(section));
  }
  entryArticle.setAttribute('aria-labelledby', 'entry-title');
}

function renderArchive(entries) {
  if (!archiveList) return;
  archiveList.innerHTML = entries.map((entry, index) => `
    <a class="archive-item" href="#entry" data-entry-index="${index}" aria-label="Read entry for ${entry.date}">
      <span>${entry.date}</span>
      <strong>${entry.title.replace(/^The Witness\s+—\s+/, '')}</strong>
    </a>
  `).join('');

  archiveList.querySelectorAll('[data-entry-index]').forEach((link) => {
    link.addEventListener('click', () => {
      const index = Number(link.dataset.entryIndex);
      const entry = entries[index];
      if (entry) {
        renderEntry(entry);
        if (latestDate) latestDate.textContent = entry.date;
        if (latestSummary) latestSummary.textContent = entry.excerpt;
      }
    });
  });
}

async function loadEntries() {
  try {
    const response = await fetch('./public/entries.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`Could not load entries.json (${response.status})`);
    const data = await response.json();
    const entries = data.entries || [];
    if (!entries.length) throw new Error('No diary entries found.');
    renderEntry(entries[0]);
    renderArchive(entries);
    if (latestDate) latestDate.textContent = entries[0].date;
    if (latestSummary) latestSummary.textContent = entries[0].excerpt;
  } catch (error) {
    console.error(error);
    setStatus('No generated entries available yet.');
  }
}

loadEntries();
