const form = document.querySelector("#search-form");
const cityInput = document.querySelector("#city-input");
const searchButton = document.querySelector("#search-button");
const message = document.querySelector("#message");
const weatherCard = document.querySelector("#weather-card");
const emptyState = document.querySelector("#empty-state");

function showMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle("error", isError);
}

function displayWeather(weather) {
  document.querySelector("#city-name").textContent = weather.city;
  document.querySelector("#country-name").textContent = weather.country;
  document.querySelector("#temperature").textContent = weather.temperature;
  document.querySelector("#feels-like").textContent = weather.feels_like;
  document.querySelector("#humidity").textContent = weather.humidity;
  document.querySelector("#wind-speed").textContent = weather.wind_speed;
  document.querySelector("#condition").textContent = weather.condition;
  document.querySelector("#condition-detail").textContent = weather.condition;

  const icon = document.querySelector("#weather-icon");
  icon.textContent = weather.icon;
  icon.setAttribute("aria-label", weather.condition);
  weatherCard.hidden = false;
  emptyState.hidden = true;
  showMessage("Showing current conditions.");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const city = cityInput.value.trim();
  if (!city) {
    showMessage("Enter a city name to search.", true);
    cityInput.focus();
    return;
  }

  searchButton.disabled = true;
  showMessage(`Checking the weather in ${city}...`);

  try {
    const response = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Unable to load weather. Please try again.");
    }
    displayWeather(result);
  } catch (error) {
    showMessage(error.message || "Unable to load weather. Please try again.", true);
  } finally {
    searchButton.disabled = false;
  }
});
