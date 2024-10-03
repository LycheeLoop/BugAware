// scripts.js

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("search-form");
    const button = document.getElementById("search-button");
    const spinner = button.querySelector(".spinner-border");

    form.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent the default form submission

        // Show spinner and disable the button
        spinner.classList.remove("d-none");
        button.setAttribute("disabled", "true");

        const formData = new FormData(form); // Gather form data

        fetch(form.action, { // Use fetch API to submit the form
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'  // Identify it as an AJAX request
            }
        })
        .then(response => response.text())  // Expect HTML response
        .then(data => {
            // Replace the results section with the new content
            document.getElementById("results-section").innerHTML = data;

            // Scroll to the results section after updating
            setTimeout(() => {
                document.getElementById("results-section").scrollIntoView({ behavior: "smooth" });
            }, 500); // Delay to allow time for the page load

            // Hide the spinner and enable the button again
            spinner.classList.add("d-none");
            button.removeAttribute("disabled");
        })
        .catch(error => {
            console.error('Error:', error);
            // Hide the spinner and enable the button again even if there's an error
            spinner.classList.add("d-none");
            button.removeAttribute("disabled");
        });
    });
});
