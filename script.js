const correctPassword = "123456"; // Set your password here

function checkPassword() {
    const input = document.getElementById("passwordInput").value;
    if (input === correctPassword) {
        document.getElementById("passwordScreen").classList.add("hidden");
        document.getElementById("mainContent").classList.remove("hidden");
    } else {
        alert("Incorrect password, please try again.");
    }
}

function selectOption(option) {
    // Placeholder for option selection handling
    console.log("Option selected:", option);
    document.getElementById("numberInput").classList.remove("hidden");
    document.getElementById("submitButton").classList.remove("hidden");
}

function generateTable() {
    // Placeholder for generating table based on inputs
    const number = document.getElementById("numberInput").value;
    console.log("Generate table for number:", number);
    // Show table or generate content here
    // For now, just showing it's selected
    const output = document.getElementById("outputTable");
    output.innerHTML = "<p>Table would be generated based on option and number: " + number + "</p>";
    output.classList.remove("hidden");
}
