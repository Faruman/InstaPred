$(document).ready(function(){
   $(".active").removeClass("active");
   var url=window.location.href.split('/');
   var name=url[url.length-1];
   if ($("#navbar_" + name).length > 0) {
       $("#navbar_" + name).addClass("active");
   } else {
       $("#navbar_home").addClass("active");
   }
});

document.querySelectorAll(".drop-zone__input").forEach((inputElement) => {
  const dropZoneElement = inputElement.closest(".drop-zone");

  dropZoneElement.addEventListener("click", (e) => {
    inputElement.click();
  });

  inputElement.addEventListener("change", (e) => {
    if (inputElement.files.length) {
      updateThumbnail(dropZoneElement, inputElement.files[0]);
    }
  });

  dropZoneElement.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZoneElement.classList.add("drop-zone--over");
  });

  ["dragleave", "dragend"].forEach((type) => {
    dropZoneElement.addEventListener(type, (e) => {
      dropZoneElement.classList.remove("drop-zone--over");
    });
  });

  dropZoneElement.addEventListener("drop", (e) => {
    e.preventDefault();

    if (e.dataTransfer.files.length) {
      inputElement.files = e.dataTransfer.files;
      updateThumbnail(dropZoneElement, e.dataTransfer.files[0]);
    }

    dropZoneElement.classList.remove("drop-zone--over");
  });
});

/**
 * Updates the thumbnail on a drop zone element.
 *
 * @param {HTMLElement} dropZoneElement
 * @param {File} file
 */
function updateThumbnail(dropZoneElement, file) {
  // First time - remove everything
  document.getElementById("processingErrorMessage").style.display = "none";

  if (dropZoneElement.querySelector(".drop-zone__prompt")) {
    dropZoneElement.querySelector(".drop-zone__prompt").remove();
  }

  if (dropZoneElement.querySelector(".drop-zone__thumb")) {
    dropZoneElement.querySelector(".drop-zone__thumb").remove()
  }

  if (dropZoneElement.querySelector(".drop-zone__thumb_error")) {
    dropZoneElement.querySelector(".drop-zone__thumb_error").remove()
  }

  // Recreate tags and show thumbnail for image files
  if (file.type.startsWith("image/")) {
    thumbnailElement = document.createElement("img");
    thumbnailElement.classList.add("drop-zone__thumb");
    dropZoneElement.appendChild(thumbnailElement);

    thumbnailElement.dataset.label = file.name;

    updateProgressBar();

    const reader = new FileReader();
    reader.readAsDataURL(file);

    reader.onload = () => {
      reader_result = reader.result;
      thumbnailElement.src = `${reader_result}`;
      processImage(dropZoneElement, reader_result).then(response => {
        if (response){
          response.json().then(data => ({data: data, status: response.status})).then(res => {
            resultsModal = $("#resultsModal");
            if (res.data.success) {
              modalText = "Number of likes predicted: <b>" + res.data.numLikes + "</b>";
              if (res.data.proposedTags.length > 0) {
                modalText = modalText + "<br><br>Recommended Tags: <br>";
                for (i in res.data.proposedTags) {
                  modalText = modalText + res.data.proposedTags[i] + "<br>";
                }
              }
            resultsModal.find(".modal-body")[0].innerHTML = modalText;
            }
            resultsModal.modal("show");
          });
        } else {
          document.getElementById("processingErrorMessage").style.display = "block";
        }
      });
    };

  } else {
    thumbnailElement = document.createElement("div");
    thumbnailElement.classList.add("drop-zone__thumb_error");
    dropZoneElement.appendChild(thumbnailElement);

    thumbnailElement.innerHTML = "Please upload a picture in the .png or .jpg format";
  }
}

async function processImage(dropZoneElement, file) {
  //send post request with image to gallery endpoint
  let formData = new FormData();
  formData.append("photo", file);

  const ctrl = new AbortController();    // timeout
  setTimeout(() => ctrl.abort(), 10000);
  try {
    let r = await fetch('/gallery',
        {method: "POST", body: formData, signal: ctrl.signal});
    return r;
  } catch (e) {
    return false;
  }
}

async function updateProgressBar() {
  progressBar = document.getElementById("imageProcessingProgressBar");
  function updateProgressBarHtml(progressBar, i){
    progressBar.innerHTML = ((i+1)*10).toString() + "% Completed";
    progressBar.style.width = ((i+1)*10).toString() + "%";
  }
  for (let i =0; i < 10; i++) {
    setTimeout(updateProgressBarHtml(progressBar, i), 1000);
  }
}