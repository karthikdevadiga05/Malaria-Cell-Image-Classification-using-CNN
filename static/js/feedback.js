// static/js/feedback.js
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("feedbackForm");
  
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const formData = new FormData(form);
  
      fetch("/contact", {
        method: "POST",
        body: formData
      })
      .then(res => res.text())
      .then(result => {
        if (result === "success") {
          Swal.fire({
            title: "✅ Thank you!",
            text: "Your feedback has been sent!",
            icon: "success"
          });
          form.reset();
        }
      });
    });
  });
  