
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
