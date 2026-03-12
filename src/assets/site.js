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
    let resistance = 0;
    let scrolling = false;
    let edgeHoldUntil = 0;
    let decayFrame = null;
    let lastWheelTime = 0;
    let edgeBottom = false;
    let edgeTop = false;

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
        panel.style.opacity = '';
        panel.classList.remove('is-stretching');
      });
      resistance = 0;
    };

    const applyStretch = (panel, offset, opacity) => {
      panel.classList.add('is-stretching');
      panel.style.transform = `translateY(${offset}px)`;
      panel.style.opacity = `${opacity}`;
    };

    const startDecay = () => {
      if (decayFrame) return;
      const maxResistance = 600;
      let prevTime = performance.now();
      const tick = (now) => {
        const dt = now - prevTime;
        prevTime = now;
        const elapsedSinceWheel = now - lastWheelTime;
        if (elapsedSinceWheel < 20) {
          decayFrame = requestAnimationFrame(tick);
          return;
        }
        resistance = Math.max(0, resistance - (dt / 5000) * maxResistance);
        const panel = resistanceDirection === 1 ? panels[panels.length - 1] : panels[0];
        if (resistance > 0 && panel) {
          const offset = resistanceDirection === 1 ? -Math.min(resistance * 0.2, 60) : Math.min(resistance * 0.2, 60);
          const opacity = Math.max(1 - resistance / 500, 0.4);
          applyStretch(panel, offset, opacity);
          decayFrame = requestAnimationFrame(tick);
        } else {
          resetStretch();
          decayFrame = null;
        }
      };
      decayFrame = requestAnimationFrame(tick);
    };

    let resistanceDirection = 1;

    const atBottomStrict = () => {
      const last = panels[panels.length - 1];
      const meta = last?.querySelector('.tribute-meta');
      const target = meta || last;
      const targetBottom = target.getBoundingClientRect().bottom;
      const viewBottom = track.getBoundingClientRect().bottom;
      return targetBottom <= viewBottom + 1;
    };

    const atTopStrict = () => track.scrollTop <= 0.5;

    track.addEventListener('scroll', () => {
      const now = Date.now();
      if (atBottomStrict()) {
        if (!edgeBottom) {
          edgeBottom = true;
          edgeHoldUntil = now + 1000;
        }
      } else {
        edgeBottom = false;
      }

      if (atTopStrict()) {
        if (!edgeTop) {
          edgeTop = true;
          edgeHoldUntil = now + 1000;
        }
      } else {
        edgeTop = false;
      }
    });

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

    document.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
        event.preventDefault();
        scrollToPanel(getCurrentIndex() + 1);
      }
      if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
        event.preventDefault();
        scrollToPanel(getCurrentIndex() - 1);
      }
    });

    track.addEventListener('wheel', (event) => {
      const lastPanel = panels[panels.length - 1];
      const lastMeta = lastPanel?.querySelector('.tribute-meta');
      const lastTarget = lastMeta || lastPanel;
      const lastTargetBottom = lastTarget.getBoundingClientRect().bottom;
      const viewBottom = track.getBoundingClientRect().bottom;
      const atBottom = lastTargetBottom <= viewBottom + 1;
      const atTop = track.scrollTop <= 0.5;
      lastWheelTime = performance.now();

      const now = Date.now();
      if (event.deltaY > 0 && atBottom) {
        event.preventDefault();
        resistanceDirection = 1;
        if (now < edgeHoldUntil) return;
        resistance += event.deltaY;
        const panel = panels[panels.length - 1];
        applyStretch(panel, -Math.min(resistance * 0.2, 60), Math.max(1 - resistance / 500, 0.4));
        if (resistance > 520 && !scrolling) {
          scrolling = true;
          resetStretch();
          edgeHoldUntil = 0;
          scrollToPanel(getCurrentIndex() + 1);
          setTimeout(() => { scrolling = false; }, 500);
        }
        startDecay();
      } else if (event.deltaY < 0 && atTop) {
        event.preventDefault();
        resistanceDirection = -1;
        if (now < edgeHoldUntil) return;
        resistance += Math.abs(event.deltaY);
        const panel = panels[0];
        applyStretch(panel, Math.min(resistance * 0.2, 60), Math.max(1 - resistance / 500, 0.4));
        if (resistance > 520 && !scrolling) {
          scrolling = true;
          resetStretch();
          edgeHoldUntil = 0;
          scrollToPanel(getCurrentIndex() - 1);
          setTimeout(() => { scrolling = false; }, 500);
        }
        startDecay();
      } else {
        resetStretch();
        edgeHoldUntil = 0;
      }
    }, { passive: false });
  });
}

function initScrollPanes() {
  const panes = [];
  const categoryPane = document.querySelector('.category-page .tribute-list');
  if (categoryPane) panes.push(categoryPane);
  const authorPane = document.querySelector('.author-page .tribute-track');
  if (authorPane) panes.push(authorPane);

  const resize = () => {
    panes.forEach((pane) => {
      const rect = pane.getBoundingClientRect();
      const available = Math.max(120, window.innerHeight - rect.top - 16);
      pane.style.height = `${available}px`;
      pane.style.maxHeight = `${available}px`;
    });
  };

  resize();
  window.addEventListener('resize', resize);
}

document.addEventListener('DOMContentLoaded', () => {
  initShuffle();
  initCarousel();
  initTributeNavigation();
  initScrollPanes();
});
