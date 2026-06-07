const root = document.documentElement;
const heroVisual = document.querySelector(".hero-visual");
let isHeroAnimated = false;

function syncHeroImage() {
    const heroImage = isHeroAnimated ? "var(--hero-image-animated)" : "var(--hero-image-static)";
    root.style.setProperty("--hero-image", heroImage);
    if (heroVisual) {
        heroVisual.setAttribute("aria-pressed", String(isHeroAnimated));
    }
}

syncHeroImage();

heroVisual?.addEventListener("click", () => {
    isHeroAnimated = !isHeroAnimated;
    syncHeroImage();
});

const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
        if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
        }
    }
}, { threshold: 0.16 });

document.querySelectorAll(".reveal").forEach((element, index) => {
    element.style.transitionDelay = `${index * 70}ms`;
    observer.observe(element);
});
