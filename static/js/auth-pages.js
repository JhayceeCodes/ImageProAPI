(function () {
    function redirectIfAuthenticated() {
        const auth = window.ImageProAuth && window.ImageProAuth.readStoredAuth
            ? window.ImageProAuth.readStoredAuth()
            : null;

        if (auth && auth.access) {
            window.location.replace("/playground/");
            return true;
        }

        return false;
    }

    function setStatus(element, message, kind) {
        element.classList.remove("hidden", "bg-red-50", "text-red-700", "bg-emerald-50", "text-emerald-700");
        if (kind === "error") {
            element.classList.add("bg-red-50", "text-red-700");
        } else {
            element.classList.add("bg-emerald-50", "text-emerald-700");
        }
        element.textContent = message;
    }

    function initAuthPages() {
        if (redirectIfAuthenticated()) {
            return;
        }

        const loginForm = document.getElementById("app-login-form");
        const registerForm = document.getElementById("app-register-form");
        const status = document.getElementById("auth-form-status");

        if (!loginForm && !registerForm) {
            return;
        }

        if (loginForm) {
            loginForm.addEventListener("submit", async (event) => {
                event.preventDefault();
                status.classList.add("hidden");

                const payload = {
                    username: document.getElementById("app-login-username").value.trim(),
                    password: document.getElementById("app-login-password").value,
                };

                try {
                    const response = await fetch("/accounts/login/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(payload),
                    });

                    const body = await response.json();
                    if (!response.ok) {
                        setStatus(status, `Login failed with status ${response.status}.`, "error");
                        return;
                    }

                    window.ImageProAuth.writeStoredAuth({
                        access: body.access,
                        refresh: body.refresh,
                    });
                    setStatus(status, "Login successful. Redirecting to the playground.", "success");
                    window.setTimeout(() => {
                        window.location.href = "/playground/";
                    }, 500);
                } catch (error) {
                    setStatus(status, String(error), "error");
                }
            });
        }

        if (registerForm) {
            registerForm.addEventListener("submit", async (event) => {
                event.preventDefault();
                status.classList.add("hidden");

                const payload = {
                    username: document.getElementById("app-register-username").value.trim(),
                    email: document.getElementById("app-register-email").value.trim(),
                    password: document.getElementById("app-register-password").value,
                };

                try {
                    const response = await fetch("/accounts/register/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(payload),
                    });

                    const body = await response.json();
                    if (!response.ok) {
                        setStatus(status, `Registration failed with status ${response.status}.`, "error");
                        return;
                    }

                    setStatus(status, "Registration successful. Redirecting to login.", "success");
                    window.setTimeout(() => {
                        window.location.href = "/login/";
                    }, 500);
                } catch (error) {
                    setStatus(status, String(error), "error");
                }
            });
        }

    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAuthPages);
    } else {
        initAuthPages();
    }
})();
