document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("resume-print")?.addEventListener("click", () => window.print());
    document.querySelector('.navbar a[href="resume.html"]')?.setAttribute("aria-current", "page");
});
