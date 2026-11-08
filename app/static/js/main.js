
// ------------------------------------
// DOCUMENT UPLOAD
// ------------------------------------

const uploadForm = document.getElementById("upload-form");

if (uploadForm) {
    uploadForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const message = document.getElementById("upload-message");
        const uploadButton = uploadForm.querySelector(
            'button[type="submit"]'
        );

        const formData = new FormData(uploadForm);

        uploadButton.disabled = true;
        uploadButton.textContent = "Uploading...";
        message.textContent = "";

        try {
            const response = await fetch("/documents/upload", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                message.textContent =
                    result.error || "Upload failed.";
                return;
            }

            message.textContent = "Document uploaded successfully!";
            uploadForm.reset();

            window.location.reload();

        } catch (error) {
            message.textContent =
                "Something went wrong. Please try again.";
        } finally {
            uploadButton.disabled = false;
            uploadButton.textContent = "Upload Document";
        }
    });
}


// ------------------------------------
// GRANT DOCUMENT PERMISSION
// ------------------------------------

const shareForms = document.querySelectorAll(".share-form");

shareForms.forEach(function (form) {
    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const message = form.nextElementSibling;
        const button = form.querySelector('button[type="submit"]');

        button.disabled = true;
        button.textContent = "Granting...";
        message.textContent = "";

        try {
            const response = await fetch(form.dataset.url, {
                method: "POST",
                body: new FormData(form)
            });

            const result = await response.json();

            if (!response.ok) {
                message.textContent =
                    result.error || "Could not grant permission.";
                return;
            }

            message.textContent =
                result.message || "Permission granted successfully!";

            setTimeout(function () {
                window.location.reload();
            }, 700);

        } catch (error) {
            message.textContent =
                "Something went wrong. Please try again.";
        } finally {
            button.disabled = false;
            button.textContent = "Grant Access";
        }
    });
});


// ------------------------------------
// REVOKE DOCUMENT PERMISSION
// ------------------------------------

const revokeButtons = document.querySelectorAll(".revoke-button");

revokeButtons.forEach(function (button) {
    button.addEventListener("click", async function () {
        const confirmed = window.confirm(
            "Are you sure you want to revoke this user's access?"
        );

        if (!confirmed) {
            return;
        }

        button.disabled = true;
        button.textContent = "Revoking...";

        try {
            const response = await fetch(button.dataset.url, {
                method: "DELETE",
                headers: {
                    "X-CSRFToken": button.dataset.csrf
                }
            });

            const result = await response.json();

            if (!response.ok) {
                alert(result.error || "Could not revoke permission.");
                button.disabled = false;
                button.textContent = "Revoke";
                return;
            }

            alert(result.message || "Permission revoked successfully!");

            window.location.reload();

        } catch (error) {
            alert("Something went wrong. Please try again.");
            button.disabled = false;
            button.textContent = "Revoke";
        }
    });
});
