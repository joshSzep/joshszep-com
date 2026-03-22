const storageKey = "joshszep-theme";
const root = document.documentElement;
const themeToggle = document.querySelector(".theme-toggle");
const heroVisual = document.querySelector(".hero-visual");
const prefersLight = window.matchMedia("(prefers-color-scheme: light)");
const heroAnimationState = {
    dark: false,
    light: false,
};

function syncHeroImage(theme) {
    const heroImage = heroAnimationState[theme] ? `var(--hero-image-animated)` : `var(--hero-image-static)`;
    root.style.setProperty("--hero-image", heroImage);
    if (heroVisual) {
        heroVisual.setAttribute("aria-pressed", String(heroAnimationState[theme]));
    }
}

function setTheme(theme) {
    root.dataset.theme = theme;
    themeToggle.textContent = theme === "light" ? "Light" : "Dark";
    themeToggle.setAttribute("aria-pressed", String(theme === "light"));
    syncHeroImage(theme);
}

const storedTheme = localStorage.getItem(storageKey);
setTheme(storedTheme || (prefersLight.matches ? "light" : "dark"));

themeToggle.addEventListener("click", () => {
    const nextTheme = root.dataset.theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem(storageKey, nextTheme);
});

heroVisual?.addEventListener("click", () => {
    const theme = root.dataset.theme === "light" ? "light" : "dark";
    heroAnimationState[theme] = !heroAnimationState[theme];
    syncHeroImage(theme);
});

prefersLight.addEventListener("change", event => {
    if (!localStorage.getItem(storageKey)) {
        setTheme(event.matches ? "light" : "dark");
    }
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