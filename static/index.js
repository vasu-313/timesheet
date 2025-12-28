const dailyActivity = document.getElementById("daily-activity");
const mysheets = document.getElementById("mysheets");

dailyActivity.addEventListener("click", () => {
    dailyActivity.classList.add("active");
    mysheets.classList.remove("active");
});

mysheets.addEventListener("click", () => {
    mysheets.classList.add("active");
    dailyActivity.classList.remove("active");
});
