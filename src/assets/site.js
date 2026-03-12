function shuffleInPlace(nodes) {
  for (let i = nodes.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [nodes[i], nodes[j]] = [nodes[j], nodes[i]];
  }
  return nodes;
}

function initShuffle() {
  document.querySelectorAll('[data-shuffle="true"]').forEach((container) => {
    const items = Array.from(container.children);
    shuffleInPlace(items).forEach((item) => container.appendChild(item));
  });
}

function initCarousel() {
  const carousel = document.querySelector('[data-carousel]');
  if (!carousel) return;

  const items = Array.from(carousel.querySelectorAll('.carousel-item'));
  if (items.length === 0) return;

  shuffleInPlace(items).forEach((item) => carousel.querySelector('.carousel-items').appendChild(item));

  let index = 0;
  const show = (i) => {
    items.forEach((item, idx) => {
      item.classList.toggle('active', idx === i);
    });
  };

  const next = () => {
    index = (index + 1) % items.length;
    show(index);
  };

  const prev = () => {
    index = (index - 1 + items.length) % items.length;
    show(index);
  };

  show(index);

  const interval = setInterval(next, 60000);
  carousel.querySelector('[data-carousel-next]').addEventListener('click', () => {
    next();
    clearInterval(interval);
  });
  carousel.querySelector('[data-carousel-prev]').addEventListener('click', () => {
    prev();
    clearInterval(interval);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      event.preventDefault();
      next();
    }
    if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault();
      prev();
    }
  });
}

function initTributeNavigation() {
  if (!document.body.classList.contains('author-page')) return;
  document.querySelectorAll('[data-tribute-track]').forEach((track) => {
    const panels = Array.from(track.querySelectorAll('.tribute-panel'));
    if (panels.length === 0) return;
    const shell = track.closest('.tribute-shell');
    const prevPage = shell?.dataset.prevPage;
    const nextPage = shell?.dataset.nextPage;
    let scrollLocked = false;
    let resistance = 0;
    let direction = 0;

    const scrollToPanel = (index) => {
      if (index < 0) {
        if (prevPage) window.location.href = prevPage;
        return;
      }
      if (index >= panels.length) {
        if (nextPage) window.location.href = nextPage;
        return;
      }
      panels[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    const getCurrentIndex = () => {
      const scrollTop = track.scrollTop;
      let current = 0;
      panels.forEach((panel, idx) => {
        if (panel.offsetTop <= scrollTop + track.clientHeight * 0.3) {
          current = idx;
        }
      });
      return current;
    };

    const resetStretch = () => {
      panels.forEach((panel) => {
        panel.style.transform = '';
        panel.classList.remove('is-stretching');
      });
      resistance = 0;
      direction = 0;
    };

    track.closest('.tribute-page').querySelectorAll('[data-tribute-next]').forEach((button) => {
      button.addEventListener('click', () => {
        scrollToPanel(getCurrentIndex() + 1);
      });
    });

    track.closest('.tribute-page').querySelectorAll('[data-tribute-prev]').forEach((button) => {
      button.addEventListener('click', () => {
        scrollToPanel(getCurrentIndex() - 1);
      });
    });

    track.querySelectorAll('.tribute-body').forEach((body) => {
      body.addEventListener('wheel', (event) => {
        if (scrollLocked) return;
        const atBottom = body.scrollTop + body.clientHeight >= body.scrollHeight - 2;
        const atTop = body.scrollTop <= 2;
        if (event.deltaY > 0 && atBottom) {
          event.preventDefault();
          direction = 1;
          resistance += event.deltaY;
          const panel = panels[getCurrentIndex()];
          panel.classList.add('is-stretching');
          panel.style.transform = `translateY(${-Math.min(resistance * 0.15, 40)}px)`;
          panel.style.opacity = `${Math.max(1 - resistance / 600, 0.6)}`;
          if (resistance > 320) {
            scrollLocked = true;
            resetStretch();
            scrollToPanel(getCurrentIndex() + 1);
            setTimeout(() => { scrollLocked = false; }, 500);
          }
        }
        if (event.deltaY < 0 && atTop) {
          event.preventDefault();
          direction = -1;
          resistance += Math.abs(event.deltaY);
          const panel = panels[getCurrentIndex()];
          panel.classList.add('is-stretching');
          panel.style.transform = `translateY(${Math.min(resistance * 0.15, 40)}px)`;
          panel.style.opacity = `${Math.max(1 - resistance / 600, 0.6)}`;
          if (resistance > 320) {
            scrollLocked = true;
            resetStretch();
            scrollToPanel(getCurrentIndex() - 1);
            setTimeout(() => { scrollLocked = false; }, 500);
          }
        }
        if (!atBottom && !atTop) resetStretch();
      }, { passive: false });
    });

    track.addEventListener('wheel', (event) => {
      if (scrollLocked) return;
      const atBottom = track.scrollTop + track.clientHeight >= track.scrollHeight - 2;
      const atTop = track.scrollTop <= 2;
      if (event.deltaY > 0 && atBottom) {
        event.preventDefault();
        direction = 1;
        resistance += event.deltaY;
        const panel = panels[getCurrentIndex()];
        panel.classList.add('is-stretching');
        panel.style.transform = `translateY(${-Math.min(resistance * 0.15, 40)}px)`;
        panel.style.opacity = `${Math.max(1 - resistance / 600, 0.6)}`;
        if (resistance > 320) {
          scrollLocked = true;
          resetStretch();
          scrollToPanel(getCurrentIndex() + 1);
          setTimeout(() => { scrollLocked = false; }, 500);
        }
      }
      if (event.deltaY < 0 && atTop) {
        event.preventDefault();
        direction = -1;
        resistance += Math.abs(event.deltaY);
        const panel = panels[getCurrentIndex()];
        panel.classList.add('is-stretching');
        panel.style.transform = `translateY(${Math.min(resistance * 0.15, 40)}px)`;
        panel.style.opacity = `${Math.max(1 - resistance / 600, 0.6)}`;
        if (resistance > 320) {
          scrollLocked = true;
          resetStretch();
          scrollToPanel(getCurrentIndex() - 1);
          setTimeout(() => { scrollLocked = false; }, 500);
        }
      }
      if (!atBottom && !atTop) resetStretch();
    }, { passive: false });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
        event.preventDefault();
        resetStretch();
        scrollToPanel(getCurrentIndex() + 1);
      }
      if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
        event.preventDefault();
        resetStretch();
        scrollToPanel(getCurrentIndex() - 1);
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initShuffle();
  initCarousel();
  initTributeNavigation();
});
