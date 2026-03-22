function shuffleInPlace(nodes) {
  for (let i = nodes.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [nodes[i], nodes[j]] = [nodes[j], nodes[i]];
  }
  return nodes;
}

function localFilePath(href) {
  if (window.location.protocol !== 'file:') return href;
  if (!href || href.startsWith('http://') || href.startsWith('https://') || href.startsWith('mailto:') || href.startsWith('#')) {
    return href;
  }
  return href.endsWith('/') ? `${href}index.html` : href;
}

function initLocalFileLinks() {
  if (window.location.protocol !== 'file:') return;

  document.querySelectorAll('a[href]').forEach((link) => {
    link.href = localFilePath(link.getAttribute('href'));
  });

  document.querySelectorAll('[data-prev-page]').forEach((node) => {
    node.dataset.prevPage = localFilePath(node.dataset.prevPage);
  });

  document.querySelectorAll('[data-next-page]').forEach((node) => {
    node.dataset.nextPage = localFilePath(node.dataset.nextPage);
  });
}

function initShuffle() {
  document.querySelectorAll('[data-shuffle="true"]').forEach((container) => {
    const fixedItems = Array.from(container.children).filter((item) => item.dataset.shuffleFixed === 'true');
    const items = Array.from(container.children).filter((item) => item.dataset.shuffleFixed !== 'true');
    container.replaceChildren(...fixedItems, ...shuffleInPlace(items));
  });
}

function initAcronyms() {
  const acronyms = Array.from(document.querySelectorAll('[data-acronym]'));
  if (acronyms.length === 0) return;

  const updatePopoverPosition = (node) => {
    const popover = node.querySelector('.acronym-popover');
    if (!popover || popover.hidden) return;
    popover.style.setProperty('--acronym-popover-shift', '0px');
    const margin = 12;
    const rect = popover.getBoundingClientRect();
    let shift = 0;
    if (rect.left < margin) {
      shift = margin - rect.left;
    } else if (rect.right > window.innerWidth - margin) {
      shift = window.innerWidth - margin - rect.right;
    }
    popover.style.setProperty('--acronym-popover-shift', `${shift}px`);
  };

  const closeAcronym = (node) => {
    const trigger = node.querySelector('.acronym-trigger');
    const popover = node.querySelector('.acronym-popover');
    if (!trigger || !popover) return;
    trigger.setAttribute('aria-expanded', 'false');
    popover.hidden = true;
    popover.style.setProperty('--acronym-popover-shift', '0px');
    node.classList.remove('is-open');
  };

  const openAcronym = (node) => {
    acronyms.forEach((item) => {
      if (item !== node) closeAcronym(item);
    });
    const trigger = node.querySelector('.acronym-trigger');
    const popover = node.querySelector('.acronym-popover');
    if (!trigger || !popover) return;
    trigger.setAttribute('aria-expanded', 'true');
    popover.hidden = false;
    node.classList.add('is-open');
    updatePopoverPosition(node);
  };

  acronyms.forEach((node) => {
    const trigger = node.querySelector('.acronym-trigger');
    const close = node.querySelector('.acronym-close');
    if (!trigger || !close) return;

    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      const isOpen = trigger.getAttribute('aria-expanded') === 'true';
      if (isOpen) {
        closeAcronym(node);
      } else {
        openAcronym(node);
      }
    });

    close.addEventListener('click', (event) => {
      event.preventDefault();
      closeAcronym(node);
      trigger.focus();
    });
  });

  document.addEventListener('click', (event) => {
    acronyms.forEach((node) => {
      if (!node.contains(event.target)) {
        closeAcronym(node);
      }
    });
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    acronyms.forEach((node) => closeAcronym(node));
  });

  window.addEventListener('resize', () => {
    acronyms.forEach((node) => updatePopoverPosition(node));
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

function initShowcase() {
  const showcase = document.querySelector('[data-showcase]');
  if (!showcase) return;

  const stage = showcase.querySelector('[data-showcase-stage]');
  const items = Array.from(stage.querySelectorAll('[data-showcase-item]'));
  if (items.length === 0) return;

  shuffleInPlace(items).forEach((item) => stage.appendChild(item));

  const gear = showcase.querySelector('[data-showcase-gear]');
  const controls = showcase.querySelector('[data-showcase-controls]');
  const speedButtons = Array.from(showcase.querySelectorAll('[data-showcase-speed]'));
  const storageKey = 'tributeShowcaseSpeed';

  const loadSpeed = () => {
    try {
      const saved = Number(window.localStorage.getItem(storageKey));
      return saved > 0 ? saved : 1;
    } catch {
      return 1;
    }
  };

  const saveSpeed = (value) => {
    try {
      window.localStorage.setItem(storageKey, String(value));
    } catch {
      // Ignore storage failures; the page still works without persistence.
    }
  };

  let speed = loadSpeed();
  let index = 0;
  let timer = null;
  const motionTimers = new Map();

  const setControlState = () => {
    speedButtons.forEach((button) => {
      button.classList.toggle('is-active', Number(button.dataset.showcaseSpeed) === speed);
    });
  };

  const setControlsOpen = (open) => {
    controls.hidden = !open;
    gear.setAttribute('aria-expanded', open ? 'true' : 'false');
  };

  const durationFor = (item) => {
    const words = Number(item.dataset.words) || 0;
    const baseSeconds = Math.max(10, Math.min(90, 6 + words / 2.8));
    return Math.round((baseSeconds * 1000) / speed);
  };

  const clearMotion = (item) => {
    const timers = motionTimers.get(item) || [];
    timers.forEach((id) => window.clearTimeout(id));
    motionTimers.delete(item);
    item.classList.remove('has-overflow');
    const tribute = item.querySelector('.showcase-tribute');
    if (tribute) {
      tribute.style.transition = '';
      tribute.style.transform = 'translateY(0)';
    }
    const progress = item.querySelector('[data-showcase-progress]');
    if (progress) {
      progress.style.transition = '';
      progress.style.transform = 'scaleX(1)';
    }
  };

  const fitCard = (item) => {
    const inner = item.querySelector('.showcase-card-inner');
    const viewport = item.querySelector('.showcase-tribute-viewport');
    const tribute = item.querySelector('.showcase-tribute');
    if (!inner || !viewport || !tribute) {
      return { displayDuration: durationFor(item), overflow: 0 };
    }

    item.classList.add('is-measuring');
    clearMotion(item);

    let tributeSize = window.innerWidth < 700 ? 28 : window.innerWidth < 1100 ? 34 : 42;
    let metaSize = window.innerWidth < 700 ? 16 : 22;
    let padding = window.innerWidth < 700 ? 24 : 40;
    let lineHeight = tributeSize > 36 ? 1.34 : 1.3;
    let attempts = 0;
    const minTributeSize = window.innerWidth < 700 ? 24 : 28;
    const minPadding = 20;
    const minMetaSize = 16;

    const apply = () => {
      inner.style.setProperty('--showcase-tribute-size', `${tributeSize}px`);
      inner.style.setProperty('--showcase-meta-size', `${metaSize}px`);
      inner.style.setProperty('--showcase-padding', `${padding}px`);
      inner.style.setProperty('--showcase-line-height', `${lineHeight}`);
    };

    apply();

    while (tribute.scrollHeight > viewport.clientHeight && attempts < 80) {
      attempts += 1;
      if (tributeSize > minTributeSize) {
        tributeSize -= 1;
      } else if (padding > minPadding) {
        padding -= 1;
      } else if (metaSize > minMetaSize) {
        metaSize -= 0.5;
      } else {
        break;
      }
      if (tributeSize <= 30) lineHeight = 1.28;
      apply();
    }

    const overflow = Math.max(0, tribute.scrollHeight - viewport.clientHeight);
    const baseDuration = durationFor(item);
    const displayDuration = overflow > 0 ? Math.max(baseDuration, 24000) : baseDuration;

    item.classList.remove('is-measuring');
    return { displayDuration, overflow };
  };

  const startMotion = (item, displayDuration, overflow) => {
    clearMotion(item);
    if (overflow <= 0) return;

    const tribute = item.querySelector('.showcase-tribute');
    if (!tribute) return;

    item.classList.add('has-overflow');
    const leadIn = 10000;
    const leadOut = 10000;
    const scrollDuration = Math.max(4000, displayDuration - leadIn - leadOut);

    const startId = window.setTimeout(() => {
      tribute.style.transition = `transform ${scrollDuration}ms linear`;
      tribute.style.transform = `translateY(-${overflow}px)`;
    }, leadIn);

    motionTimers.set(item, [startId]);
  };

  const scheduleNext = (displayDuration) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      show((index + 1) % items.length);
    }, displayDuration);
  };

  const show = (nextIndex) => {
    const nextItem = items[nextIndex];
    items.forEach((item) => clearMotion(item));
    const layout = fitCard(nextItem);
    startMotion(nextItem, layout.displayDuration, layout.overflow);
    const progress = nextItem.querySelector('[data-showcase-progress]');
    if (progress) {
      progress.style.transform = 'scaleX(1)';
      // Force layout so the timer bar reliably restarts on repeated shows.
      progress.getBoundingClientRect();
      progress.style.transition = `transform ${layout.displayDuration}ms linear`;
      progress.style.transform = 'scaleX(0)';
    }
    items.forEach((item, itemIndex) => {
      item.classList.toggle('is-active', itemIndex === nextIndex);
    });
    index = nextIndex;
    scheduleNext(layout.displayDuration);
  };

  gear.addEventListener('click', () => {
    setControlsOpen(controls.hidden);
  });

  document.addEventListener('click', (event) => {
    if (!showcase.contains(event.target)) {
      setControlsOpen(false);
    }
  });

  speedButtons.forEach((button) => {
    button.addEventListener('click', () => {
      speed = Number(button.dataset.showcaseSpeed) || 1;
      saveSpeed(speed);
      setControlState();
      show(index);
    });
  });

  window.addEventListener('resize', () => {
    show(index);
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      window.clearTimeout(timer);
    } else {
      scheduleNext();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown' || event.key === ' ') {
      event.preventDefault();
      show((index + 1) % items.length);
    }
    if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault();
      show((index - 1 + items.length) % items.length);
    }
  });

  setControlState();
  setControlsOpen(false);
  show(0);
}

document.addEventListener('DOMContentLoaded', () => {
  initLocalFileLinks();
  initShuffle();
  initAcronyms();
  initCarousel();
  initTributeNavigation();
  initScrollPanes();
  initShowcase();
});
