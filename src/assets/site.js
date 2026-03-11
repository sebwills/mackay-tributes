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
}

function initTributeNavigation() {
  document.querySelectorAll('[data-tribute-track]').forEach((track) => {
    const panels = Array.from(track.querySelectorAll('.tribute-panel'));
    if (panels.length === 0) return;

    const scrollToPanel = (index) => {
      if (index < 0 || index >= panels.length) return;
      panels[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    track.closest('.tribute-page').querySelectorAll('[data-tribute-next]').forEach((button) => {
      button.addEventListener('click', () => {
        const current = panels.findIndex((panel) => {
          const rect = panel.getBoundingClientRect();
          return rect.top >= 0 && rect.top < window.innerHeight * 0.5;
        });
        scrollToPanel(current + 1);
      });
    });

    track.closest('.tribute-page').querySelectorAll('[data-tribute-prev]').forEach((button) => {
      button.addEventListener('click', () => {
        const current = panels.findIndex((panel) => {
          const rect = panel.getBoundingClientRect();
          return rect.top >= 0 && rect.top < window.innerHeight * 0.5;
        });
        scrollToPanel(current - 1);
      });
    });

    track.querySelectorAll('.tribute-body').forEach((body) => {
      body.addEventListener('wheel', (event) => {
        const atBottom = body.scrollTop + body.clientHeight >= body.scrollHeight - 2;
        const atTop = body.scrollTop <= 2;
        if (event.deltaY > 0 && atBottom) {
          event.preventDefault();
          const panel = body.closest('.tribute-panel');
          const index = panels.indexOf(panel);
          scrollToPanel(index + 1);
        }
        if (event.deltaY < 0 && atTop) {
          event.preventDefault();
          const panel = body.closest('.tribute-panel');
          const index = panels.indexOf(panel);
          scrollToPanel(index - 1);
        }
      }, { passive: false });
    });

    document.addEventListener('keydown', (event) => {
      if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
      const current = panels.findIndex((panel) => {
        const rect = panel.getBoundingClientRect();
        return rect.top >= 0 && rect.top < window.innerHeight * 0.5;
      });
      if (event.key === 'ArrowDown') scrollToPanel(current + 1);
      if (event.key === 'ArrowUp') scrollToPanel(current - 1);
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initShuffle();
  initCarousel();
  initTributeNavigation();
});
