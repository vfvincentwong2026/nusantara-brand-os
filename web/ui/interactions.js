/* Nusantara Brand OS · Saffron 交互层（共享）
   磁吸光标（仅精确指针设备）+ 滚动渐显（Fade+Slide-up 24px / 0.6s）
   依赖 tokens.css 的 .cursor-dot/.cursor-ring/.rv 样式；reduced-motion 自动降级 */
(() => {
  const fine = matchMedia('(pointer:fine)').matches &&
               !matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (fine) {
    document.body.classList.add('cursor-on');
    const dot = document.createElement('div'), ring = document.createElement('div');
    dot.className = 'cursor-dot'; ring.className = 'cursor-ring';
    document.body.append(dot, ring);
    let mx = innerWidth / 2, my = innerHeight / 2, rx = mx, ry = my;
    addEventListener('pointermove', e => {
      mx = e.clientX; my = e.clientY;
      dot.style.transform = `translate(${mx - 3}px,${my - 3}px)`;
    });
    (function loop() {
      rx += (mx - rx) * .16; ry += (my - ry) * .16;
      const s = ring.classList.contains('big') ? 56 : 34;
      ring.style.transform = `translate(${rx - s / 2}px,${ry - s / 2}px)`;
      requestAnimationFrame(loop);
    })();
    document.querySelectorAll('a,button').forEach(el => {
      el.addEventListener('pointerenter', () => ring.classList.add('big'));
      el.addEventListener('pointerleave', () => ring.classList.remove('big'));
    });
  }

  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('rv-in'); io.unobserve(e.target); }
  }), { threshold: .08, rootMargin: '0px 0px -4% 0px' });
  document.querySelectorAll(
    '.head,.hero-grid,.stats,.panel,.card,.fmt,.tier,.portal,.ed-row,.marquee,.partner .tags,.ed-sec,.rules,.layout,.plan'
  ).forEach(el => { el.classList.add('rv'); io.observe(el); });
})();
