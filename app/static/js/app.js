document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".password-toggle").forEach((button) => {
        button.addEventListener("click", () => {
            const targetId = button.getAttribute("data-target");
            const input = targetId ? document.getElementById(targetId) : null;
            if (!input) {
                return;
            }
            const icon = button.querySelector("i");
            const isPassword = input.type === "password";
            input.type = isPassword ? "text" : "password";
            if (icon) {
                icon.className = isPassword ? "bi bi-eye-slash" : "bi bi-eye";
            }
        });
    });

    document.querySelectorAll(".persist-check").forEach((checkbox) => {
        const key = checkbox.getAttribute("data-key");
        if (!key) {
            return;
        }
        const saved = window.localStorage.getItem(key);
        checkbox.checked = saved === "1";
        checkbox.addEventListener("change", () => {
            window.localStorage.setItem(key, checkbox.checked ? "1" : "0");
        });
    });

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    document.querySelectorAll(".speech-fill").forEach((button) => {
        button.addEventListener("click", () => {
            if (!SpeechRecognition) {
                alert("Speech recognition is not supported in this browser.");
                return;
            }
            const targetId = button.getAttribute("data-target");
            const mode = (button.getAttribute("data-mode") || "replace").toLowerCase();
            const input = targetId ? document.getElementById(targetId) : null;
            if (!input) {
                return;
            }

            const recognition = new SpeechRecognition();
            recognition.lang = "en-IN";
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            const originalHtml = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i class="bi bi-mic-fill text-danger"></i>';

            recognition.onresult = (event) => {
                const text = event.results?.[0]?.[0]?.transcript || "";
                if (!text) {
                    return;
                }
                if (mode === "append" && input.value) {
                    const joiner = input.tagName === "TEXTAREA" ? ", " : " ";
                    input.value = `${input.value}${joiner}${text}`.trim();
                } else {
                    input.value = text.trim();
                }
            };
            recognition.onerror = () => {
                alert("Unable to capture speech. Please try again.");
            };
            recognition.onend = () => {
                button.disabled = false;
                button.innerHTML = originalHtml;
            };
            recognition.start();
        });
    });

    const tripForm = document.getElementById("trip-form");
    const locationPattern = /^[A-Za-z][A-Za-z\s,.'-]{1,118}$/;

    const sanitizeLocationText = (value) => {
        if (!value) {
            return "";
        }
        return value
            .replace(/[^A-Za-z\s,.'-]/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    };

    const bestLocationName = (address) => {
        if (!address) {
            return "";
        }
        return sanitizeLocationText(
            address.city || address.town || address.village || address.suburb || address.county || address.state || address.country || ""
        );
    };

    const bestStateCountry = (address) => {
        if (!address) {
            return "";
        }
        const state = sanitizeLocationText(address.state || address.state_district || address.county || "");
        const country = sanitizeLocationText(address.country || "");
        if (state && country) {
            return `${state}, ${country}`;
        }
        return state || country;
    };

    const uniqueNonEmpty = (items) => {
        const seen = new Set();
        const out = [];
        items.forEach((item) => {
            const value = (item || "").trim();
            if (!value) {
                return;
            }
            const key = value.toLowerCase();
            if (seen.has(key)) {
                return;
            }
            seen.add(key);
            out.push(value);
        });
        return out;
    };

    const setDatalistOptions = (datalist, options) => {
        if (!datalist) {
            return;
        }
        datalist.innerHTML = "";
        options.forEach((optionValue) => {
            const option = document.createElement("option");
            option.value = optionValue;
            datalist.appendChild(option);
        });
    };

    const debounce = (fn, waitMs = 280) => {
        let timer = null;
        return (...args) => {
            if (timer) {
                clearTimeout(timer);
            }
            timer = setTimeout(() => fn(...args), waitMs);
        };
    };

    const fetchGeoSuggestions = async (query) => {
        const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=8&language=en&format=json`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Geo suggestion request failed");
        }
        const data = await response.json();
        return Array.isArray(data?.results) ? data.results : [];
    };

    const attachPlaceAutocomplete = (inputSelector, datalistSelector, toSuggestion) => {
        const input = document.querySelector(inputSelector);
        const datalist = document.querySelector(datalistSelector);
        if (!input || !datalist) {
            return;
        }

        const onInputDebounced = debounce(async () => {
            const query = (input.value || "").trim();
            if (query.length < 2) {
                setDatalistOptions(datalist, []);
                return;
            }

            try {
                const results = await fetchGeoSuggestions(query);
                const options = uniqueNonEmpty(
                    results.map((item) => sanitizeLocationText(toSuggestion(item))).filter(Boolean)
                );
                setDatalistOptions(datalist, options.slice(0, 8));
            } catch (_error) {
                setDatalistOptions(datalist, []);
            }
        }, 260);

        input.addEventListener("input", onInputDebounced);
    };

    attachPlaceAutocomplete("#fromLocationInput", "#fromLocationSuggestions", (item) => {
        return item?.name || "";
    });

    attachPlaceAutocomplete("#stateCountryInput", "#stateCountrySuggestions", (item) => {
        const admin = item?.admin1 || item?.admin2 || "";
        const country = item?.country || "";
        return [admin, country].filter(Boolean).join(", ");
    });

    const fillApproxFromIp = async (fromInput, stateInput) => {
        const response = await fetch("https://ipapi.co/json/");
        if (!response.ok) {
            throw new Error("IP location request failed");
        }
        const data = await response.json();
        const city = sanitizeLocationText(data.city || "");
        const region = sanitizeLocationText(data.region || "");
        const country = sanitizeLocationText(data.country_name || "");

        if (city) {
            fromInput.value = city;
        } else {
            fromInput.value = "Current Location";
        }

        if (region && country) {
            stateInput.value = `${region}, ${country}`;
        } else if (country) {
            stateInput.value = country;
        } else if (region) {
            stateInput.value = region;
        }
    };

    document.querySelectorAll(".use-current-location").forEach((button) => {
        button.addEventListener("click", () => {
            const form = button.closest("form");
            const fromInput = form?.querySelector('input[name="from_location"]');
            const stateInput = form?.querySelector('input[name="state_country"]');

            if (!fromInput || !stateInput) {
                return;
            }
            if (!navigator.geolocation) {
                alert("Geolocation is not supported in this browser.");
                return;
            }

            const originalLabel = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Locating...';

            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    try {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`;
                        const response = await fetch(url);
                        if (!response.ok) {
                            throw new Error("Reverse geocode request failed");
                        }
                        const data = await response.json();
                        const addr = data.address || {};
                        const locationName = bestLocationName(addr) || "Current Location";
                        const stateCountry = bestStateCountry(addr);

                        fromInput.value = locationName;
                        if (stateCountry) {
                            stateInput.value = stateCountry;
                        }
                    } catch (error) {
                        fromInput.value = "Current Location";
                        alert("Location captured, but place name lookup failed. Please verify fields once.");
                    } finally {
                        button.disabled = false;
                        button.innerHTML = originalLabel;
                    }
                },
                async (error) => {
                    try {
                        await fillApproxFromIp(fromInput, stateInput);
                        if (error && error.code === 1) {
                            alert("GPS permission denied. Used approximate location from network.");
                        } else {
                            alert("GPS unavailable. Used approximate location from network.");
                        }
                    } catch (_ipError) {
                        alert("Location access denied or unavailable. Please enter location manually.");
                    } finally {
                        button.disabled = false;
                        button.innerHTML = originalLabel;
                    }
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        });
    });

    if (tripForm) {
        const startDateInput = tripForm.querySelector('input[name="start_date"]');
        if (startDateInput) {
            const today = new Date().toISOString().split("T")[0];
            startDateInput.min = today;
        }

        tripForm.addEventListener("submit", (event) => {
            const destinationsInput = tripForm.querySelector('textarea[name="destinations"]');
            if (!destinationsInput || !destinationsInput.value.trim()) {
                event.preventDefault();
                alert("Please add at least one destination.");
                return;
            }

            const destinations = destinationsInput.value
                .split(/[,\n]/)
                .map((item) => item.trim())
                .filter(Boolean);

            const fromLocation = (tripForm.querySelector('input[name="from_location"]')?.value || "").trim();
            const stateCountry = (tripForm.querySelector('input[name="state_country"]')?.value || "").trim();
            const daysValue = Number(tripForm.querySelector('input[name="number_of_days"]')?.value || 0);

            if (!locationPattern.test(fromLocation)) {
                event.preventDefault();
                alert("From Location must be a valid place name (letters only).");
                return;
            }

            if (!locationPattern.test(stateCountry)) {
                event.preventDefault();
                alert("State/Country must be a valid place name (letters only).");
                return;
            }

            const invalidDestination = destinations.find((name) => !locationPattern.test(name));
            if (invalidDestination) {
                event.preventDefault();
                alert(`Destination '${invalidDestination}' is invalid. Use place names only.`);
                return;
            }

            if (daysValue > 0 && destinations.length > daysValue) {
                event.preventDefault();
                alert("Number of days must be at least equal to destination count.");
                return;
            }

            if (destinations.length > 8) {
                event.preventDefault();
                alert("Please keep destinations to 8 or fewer for better plans.");
            }
        });
    }
});
