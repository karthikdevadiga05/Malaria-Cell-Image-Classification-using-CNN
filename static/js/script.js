document.addEventListener("DOMContentLoaded", () => {
    const resultContainer = document.querySelector(".result-container");
  
    // 📥 Handle PDF Download on Result Page
    const pdfBtn = document.querySelector(".download-btns .submit-btn");
    
  
    if (resultContainer && pdfBtn) {
      const script1 = document.createElement("script");
      script1.src = "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js";
      document.body.appendChild(script1);
  
      const script2 = document.createElement("script");
      script2.src = "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js";
      script2.onload = () => {
        window.jsPDF = window.jspdf.jsPDF;
  
        pdfBtn.addEventListener("click", () => {
          html2canvas(resultContainer).then(canvas => {
            const imgData = canvas.toDataURL("image/png");
            const pdf = new jsPDF();
            const pageWidth = pdf.internal.pageSize.getWidth();
            const imgProps = pdf.getImageProperties(imgData);
            const pdfHeight = (imgProps.height * pageWidth) / imgProps.width;
            pdf.addImage(imgData, "PNG", 0, 10, pageWidth, pdfHeight);
            pdf.save("malaria_result.pdf");
          });
        });
      };
      document.body.appendChild(script2);
    }
  
    // 🖼️ Image Preview on Upload Page
    const fileInput = document.getElementById("file-input");
    const imagePreview = document.getElementById("image-preview");
    const fileName = document.getElementById("file-name");
  
    if (fileInput && imagePreview && fileName) {
      fileInput.addEventListener("change", function () {
        const file = this.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = function (e) {
            imagePreview.style.display = "block";
            imagePreview.src = e.target.result;
            fileName.textContent = file.name;
          };
          reader.readAsDataURL(file);
        } else {
          imagePreview.style.display = "none";
          imagePreview.src = "#";
          fileName.textContent = "Choose an image";
        }
      });
    }
  
    // 🧠 Animate Upload Section on Scroll (ALWAYS re-animate)
const uploadSection = document.querySelector(".upload-section");

function triggerUploadAnimation() {
  if (uploadSection) {
    uploadSection.classList.remove("visible");
    void uploadSection.offsetWidth; // force reflow
    uploadSection.classList.add("visible");
  }
}

const uploadBtn = document.querySelector(".btn-glow");

if (uploadBtn && uploadSection) {
  uploadBtn.addEventListener("click", e => {
    e.preventDefault();

    // Step 1: Add temporary reset class to disable transition
    uploadSection.classList.remove("visible");
    uploadSection.classList.add("reset-anim");

    // Step 2: Scroll into view
    uploadSection.scrollIntoView({ behavior: "smooth", block: "start" });

    // Step 3: After short delay, remove reset and add visible to animate
    setTimeout(() => {
      uploadSection.classList.remove("reset-anim");
      void uploadSection.offsetWidth;
      uploadSection.classList.add("visible");
    }, 500); // matches scroll duration
  });
}



  });
  