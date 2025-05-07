document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("upload-form");

  if (uploadForm) {
    // Initialize form functions
    initGlobalFormFunctions();

    uploadForm.addEventListener("submit", function (e) {
      const submitBtn = e.submitter;

      // Debugging
      console.log("Form submission detected");
      console.log(
        "Submit button name:",
        submitBtn ? submitBtn.name : "unknown"
      );

      // If this is the initial "Upload Marks" submission
      if (submitBtn && submitBtn.name === "upload_marks") {
        console.log("Upload Marks button clicked");

        // Get all form values
        const formData = {
          education_level: document.getElementById("education_level").value,
          subject: document.getElementById("subject").value,
          grade: document.getElementById("grade").value,
          stream: document.getElementById("stream").value,
          term: document.getElementById("term").value,
          assessment_type: document.getElementById("assessment_type").value,
          total_marks: document.getElementById("total_marks").value,
        };

        console.log("Form data being submitted:", formData);

        // Validate all required fields
        const requiredFields = uploadForm.querySelectorAll("[required]");
        let isValid = true;

        requiredFields.forEach((field) => {
          console.log(`Checking field: ${field.name}, value: ${field.value}`);
          if (!field.value) {
            field.closest(".form-group").classList.add("error");
            isValid = false;
          } else {
            field.closest(".form-group").classList.remove("error");
          }
        });

        if (!isValid) {
          e.preventDefault();
          console.log("Form validation failed");
          alert("Please fill in all required fields before uploading marks.");
          return;
        }

        console.log(
          "Form validation passed, submitting form for student data..."
        );

        // Form will submit naturally
      }
    });

    // Handle submit_marks form validation if present
    const marksForm = document.querySelector('form[name="submit_marks"]');
    if (marksForm) {
      marksForm.addEventListener("submit", function (e) {
        console.log("Marks submission form detected");

        // Validate all mark inputs
        const markInputs = marksForm.querySelectorAll('input[type="number"]');
        let isValid = true;

        markInputs.forEach((input) => {
          const value = input.value.trim();
          const maxMarks = parseInt(input.getAttribute("max"), 10);

          if (!value || isNaN(parseInt(value, 10))) {
            input.classList.add("error");
            isValid = false;
          } else if (
            parseInt(value, 10) < 0 ||
            parseInt(value, 10) > maxMarks
          ) {
            input.classList.add("error");
            isValid = false;
          } else {
            input.classList.remove("error");
          }
        });

        if (!isValid) {
          e.preventDefault();
          console.log("Marks validation failed");
          alert(
            "Please ensure all marks are valid and within the allowed range."
          );
          return;
        }

        console.log("Marks validation passed, submitting...");
      });
    }

    // Real-time validation
    const inputs = document.querySelectorAll("input, select");
    inputs.forEach((input) => {
      input.addEventListener("change", function () {
        if (this.value) {
          this.closest(".form-group")?.classList.remove("error");
          this.classList.remove("error");
        } else {
          this.closest(".form-group")?.classList.add("error");
          this.classList.add("error");
        }
      });
    });
  }
});

// Initialize global functions for form updates
function initGlobalFormFunctions() {
  console.log("\n=== INITIALIZING GLOBAL FORM FUNCTIONS ===");

  // Define updateSubjects function globally
  window.updateSubjects = function () {
    console.log("\n=== UPDATING SUBJECTS ===");
    const educationLevelSelect = document.getElementById("education_level");
    const subjectSelect = document.getElementById("subject");

    if (!educationLevelSelect || !subjectSelect) {
      console.error("Required select elements not found");
      return;
    }

    const selectedEducationLevel = educationLevelSelect.value;
    console.log(`Education level changed to: ${selectedEducationLevel}`);

    // Clear existing options
    subjectSelect.innerHTML = '<option value="">Select Subject</option>';

    // Get the form group for styling
    const formGroup = subjectSelect.closest(".form-group");

    if (selectedEducationLevel) {
      let subjects = [];
      switch (selectedEducationLevel) {
        case "lower_primary":
          subjects = [
            "Indigenous Language",
            "Kiswahili",
            "Mathematics",
            "English",
            "Religious Education",
            "Environmental Activities",
            "Creative Activities",
          ];
          break;
        case "upper_primary":
          subjects = [
            "English",
            "Mathematics",
            "Kiswahili",
            "Religious Education",
            "Agriculture and Nutrition",
            "Social Studies",
            "Creative Arts",
            "Science and Technology",
          ];
          break;
        case "junior_secondary":
          subjects = [
            "Social Studies and Life Skills",
            "Agriculture and Home Science",
            "Integrated Science and Health Education",
            "Pre-Technical Studies",
            "Visual Arts",
            "Mathematics",
            "English",
            "Kiswahili",
            "Religious Education",
          ];
          break;
      }

      console.log(
        `Populating subjects for ${selectedEducationLevel}:`,
        subjects
      );

      // Add the new options
      subjects.forEach((subject) => {
        const option = document.createElement("option");
        option.value = subject;
        option.textContent = subject;
        subjectSelect.appendChild(option);
      });

      formGroup.classList.add("success");
      formGroup.classList.remove("error");
    } else {
      console.log("No education level selected - clearing subjects");
      formGroup.classList.remove("success");
    }
  };

  // Define updateStreams function globally
  window.updateStreams = function () {
    console.log("\n=== GRADE CHANGE DETECTED ===");
    const gradeSelect = document.getElementById("grade");
    const streamSelect = document.getElementById("stream");

    if (!gradeSelect || !streamSelect) {
      console.error("Grade or stream select elements not found");
      return;
    }

    const selectedGrade = gradeSelect.value;
    console.log(`Grade changed to: ${selectedGrade}`);

    // Clear existing options
    streamSelect.innerHTML = '<option value="">Select Stream</option>';

    // Get the form group for styling
    const formGroup = streamSelect.closest(".form-group");

    if (selectedGrade) {
      const streams = ["B", "G", "Y"];
      console.log(`Populating streams for grade ${selectedGrade}:`, streams);

      // Add the new options
      streams.forEach((stream) => {
        const option = document.createElement("option");
        option.value = `${selectedGrade}${stream}`;
        option.textContent = `${selectedGrade}${stream}`;
        streamSelect.appendChild(option);
      });

      formGroup.classList.add("success");
      formGroup.classList.remove("error");
    } else {
      console.log("No grade selected - clearing streams");
      formGroup.classList.remove("success");
    }
  };

  // Connect event listeners to form elements if they exist
  const educationLevelSelect = document.getElementById("education_level");
  if (educationLevelSelect) {
    educationLevelSelect.addEventListener("change", window.updateSubjects);
    // Run initial update if value is already selected
    if (educationLevelSelect.value) {
      console.log("Initial education level value detected - updating subjects");
      window.updateSubjects();
    }
  }

  const gradeSelect = document.getElementById("grade");
  if (gradeSelect) {
    gradeSelect.addEventListener("change", window.updateStreams);
    // Run initial update if value is already selected
    if (gradeSelect.value) {
      console.log("Initial grade value detected - updating streams");
      window.updateStreams();
    }
  }

  console.log("Global form functions initialized successfully");
}

// Function to show debug information
function showDebug(message) {
  const debugDiv = document.getElementById("debug-info");
  const debugContent = document.getElementById("debug-content");
  if (debugDiv && debugContent) {
    debugContent.innerHTML += message + "<br>";
    debugDiv.style.display = "block";
  } else {
    console.log("Debug message:", message);
  }
}
