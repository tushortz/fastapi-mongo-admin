(function () {
  "use strict";

  var COOKIE_MAX_AGE = 60 * 60 * 24 * 365;
  var html = document.documentElement;

  function setCookie(name, value) {
    document.cookie =
      name + "=" + encodeURIComponent(value) +
      ";path=/;max-age=" + COOKIE_MAX_AGE + ";SameSite=Lax";
  }

  function applyTheme(theme) {
    if (theme !== "light" && theme !== "dark") {
      return;
    }
    html.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("admin_theme", theme);
    } catch (e) {
      /* ignore */
    }
    setCookie("admin_theme", theme);
  }

  function initTheme() {
    var stored = null;
    try {
      stored = localStorage.getItem("admin_theme");
    } catch (e) {
      /* ignore */
    }
    var serverTheme = html.getAttribute("data-theme") || "light";
    if (stored && (stored === "light" || stored === "dark") && stored !== serverTheme) {
      applyTheme(stored);
    }
  }

  function initThemeToggle() {
    var toggle = document.getElementById("theme-toggle");
    if (!toggle) {
      return;
    }
    toggle.addEventListener("click", function () {
      var current = html.getAttribute("data-theme") || "light";
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }

  function initFilterDrawer() {
    var toggle = document.getElementById("filter-toggle");
    var drawer = document.getElementById("filter-drawer");
    var backdrop = document.getElementById("filter-backdrop");
    var closeBtn = drawer ? drawer.querySelector(".filter-drawer__close") : null;
    if (!toggle || !drawer || !backdrop) {
      return;
    }

    function openDrawer() {
      drawer.hidden = false;
      backdrop.hidden = false;
      requestAnimationFrame(function () {
        drawer.classList.add("is-open");
        backdrop.classList.add("is-open");
      });
      toggle.setAttribute("aria-expanded", "true");
      document.body.classList.add("filter-drawer-open");
    }

    function closeDrawer() {
      drawer.classList.remove("is-open");
      backdrop.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      document.body.classList.remove("filter-drawer-open");
      window.setTimeout(function () {
        if (!drawer.classList.contains("is-open")) {
          drawer.hidden = true;
          backdrop.hidden = true;
        }
      }, 200);
    }

    toggle.addEventListener("click", function () {
      if (drawer.classList.contains("is-open")) {
        closeDrawer();
      } else {
        openDrawer();
      }
    });

    backdrop.addEventListener("click", closeDrawer);

    if (closeBtn) {
      closeBtn.addEventListener("click", closeDrawer);
    }

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && drawer.classList.contains("is-open")) {
        closeDrawer();
      }
    });
  }

  function initRelatedSelects() {
    var containers = document.querySelectorAll(".related-select");
    containers.forEach(function (container) {
      var lookupUrl = container.getAttribute("data-lookup-url");
      var minChars = parseInt(container.getAttribute("data-min-chars") || "2", 10);
      var hidden = container.querySelector('input[type="hidden"]');
      var search = container.querySelector(".related-select__search");
      var results = container.querySelector(".related-select__results");
      if (!lookupUrl || !hidden || !search || !results) {
        return;
      }

      var selectedLabel = search.value || "";
      var debounceTimer = null;

      function closeResults() {
        results.hidden = true;
        results.innerHTML = "";
        search.setAttribute("aria-expanded", "false");
      }

      function selectOption(value, label) {
        hidden.value = value;
        search.value = label;
        selectedLabel = label;
        closeResults();
      }

      function renderResults(items) {
        results.innerHTML = "";
        if (!items.length) {
          closeResults();
          return;
        }
        items.forEach(function (item) {
          var li = document.createElement("li");
          li.className = "related-select__option";
          li.setAttribute("role", "option");
          li.textContent = item.label;
          li.addEventListener("mousedown", function (event) {
            event.preventDefault();
            selectOption(item.value, item.label);
          });
          results.appendChild(li);
        });
        results.hidden = false;
        search.setAttribute("aria-expanded", "true");
      }

      function fetchResults(query) {
        var url = lookupUrl + "?q=" + encodeURIComponent(query);
        fetch(url, { headers: { Accept: "application/json" }, credentials: "same-origin" })
          .then(function (response) {
            if (!response.ok) {
              throw new Error("lookup failed");
            }
            return response.json();
          })
          .then(function (data) {
            renderResults(data.results || []);
          })
          .catch(function () {
            closeResults();
          });
      }

      search.addEventListener("input", function () {
        var query = search.value.trim();
        hidden.value = "";
        window.clearTimeout(debounceTimer);
        if (query.length < minChars) {
          closeResults();
          return;
        }
        debounceTimer = window.setTimeout(function () {
          fetchResults(query);
        }, 300);
      });

      search.addEventListener("blur", function () {
        window.setTimeout(function () {
          if (!hidden.value) {
            if (!search.value.trim()) {
              selectedLabel = "";
              return;
            }
            search.value = selectedLabel;
            return;
          }
          if (!search.value.trim()) {
            hidden.value = "";
            selectedLabel = "";
          }
        }, 150);
      });

      search.addEventListener("focus", function () {
        var query = search.value.trim();
        if (query.length >= minChars && !results.children.length) {
          fetchResults(query);
        }
      });

      document.addEventListener("click", function (event) {
        if (!container.contains(event.target)) {
          closeResults();
        }
      });
    });
  }

  function initTagInputs() {
    document.querySelectorAll(".tag-input").forEach(function (container) {
      var hidden = container.querySelector('input[type="hidden"]');
      var entry = container.querySelector(".tag-input__entry");
      var tagsEl = container.querySelector(".tag-input__tags");
      if (!hidden || !entry || !tagsEl) {
        return;
      }

      var tags = [];
      try {
        tags = JSON.parse(container.getAttribute("data-initial") || "[]");
      } catch (error) {
        tags = [];
      }
      if (!Array.isArray(tags)) {
        tags = [];
      }

      function syncHidden() {
        hidden.value = JSON.stringify(tags);
      }

      function renderTags() {
        tagsEl.innerHTML = "";
        tags.forEach(function (tag, index) {
          var chip = document.createElement("span");
          chip.className = "tag-input__tag";
          chip.appendChild(document.createTextNode(String(tag)));

          var removeBtn = document.createElement("button");
          removeBtn.type = "button";
          removeBtn.className = "tag-input__remove";
          removeBtn.setAttribute("aria-label", "Remove tag");
          removeBtn.textContent = "\u00d7";
          removeBtn.addEventListener("click", function () {
            tags.splice(index, 1);
            renderTags();
          });

          chip.appendChild(removeBtn);
          tagsEl.appendChild(chip);
        });
        syncHidden();
      }

      function addTag(rawValue) {
        var value = String(rawValue).trim();
        if (!value || tags.indexOf(value) !== -1) {
          return;
        }
        tags.push(value);
        renderTags();
      }

      entry.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === ",") {
          event.preventDefault();
          addTag(entry.value.replace(/,/g, ""));
          entry.value = "";
        } else if (event.key === "Backspace" && !entry.value && tags.length) {
          tags.pop();
          renderTags();
        }
      });

      entry.addEventListener("blur", function () {
        if (entry.value.trim()) {
          addTag(entry.value);
          entry.value = "";
        }
      });

      renderTags();
    });
  }

  function initDataTransferDrawer() {
    var toggle = document.getElementById("data-transfer-toggle");
    var drawer = document.getElementById("data-transfer-drawer");
    var backdrop = document.getElementById("data-transfer-backdrop");
    var closeBtn = drawer ? drawer.querySelector(".data-transfer-drawer__close") : null;
    var exportForm = document.getElementById("data-export-form");
    if (!toggle || !drawer || !backdrop) {
      return;
    }

    function openDrawer() {
      drawer.hidden = false;
      backdrop.hidden = false;
      requestAnimationFrame(function () {
        drawer.classList.add("is-open");
        backdrop.classList.add("is-open");
      });
      toggle.setAttribute("aria-expanded", "true");
      document.body.classList.add("data-transfer-drawer-open");
    }

    function closeDrawer() {
      drawer.classList.remove("is-open");
      backdrop.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      document.body.classList.remove("data-transfer-drawer-open");
      window.setTimeout(function () {
        if (!drawer.classList.contains("is-open")) {
          drawer.hidden = true;
          backdrop.hidden = true;
        }
      }, 200);
    }

    if (drawer.classList.contains("is-open")) {
      openDrawer();
    }

    toggle.addEventListener("click", function () {
      if (drawer.classList.contains("is-open")) {
        closeDrawer();
      } else {
        openDrawer();
      }
    });

    backdrop.addEventListener("click", closeDrawer);

    if (closeBtn) {
      closeBtn.addEventListener("click", closeDrawer);
    }

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && drawer.classList.contains("is-open")) {
        closeDrawer();
      }
    });

    if (exportForm) {
      exportForm.addEventListener("submit", function (event) {
        var scopeInput = exportForm.querySelector('input[name="scope"]:checked');
        var scope = scopeInput ? scopeInput.value : "selected";
        var holder = document.getElementById("data-export-selected-ids");
        if (!holder) {
          return;
        }
        holder.innerHTML = "";
        if (scope !== "selected") {
          return;
        }
        var selected = document.querySelectorAll(
          '#changelist-form input[name="_selected_action"]:checked'
        );
        if (!selected.length) {
          event.preventDefault();
          var message = exportForm.getAttribute("data-select-rows-message") || "Select at least one row.";
          window.alert(message);
          return;
        }
        selected.forEach(function (checkbox) {
          var input = document.createElement("input");
          input.type = "hidden";
          input.name = "_selected_action";
          input.value = checkbox.value;
          holder.appendChild(input);
        });
      });
    }
  }

  initTheme();
  document.addEventListener("DOMContentLoaded", function () {
    initThemeToggle();
    initFilterDrawer();
    initDataTransferDrawer();
    initRelatedSelects();
    initTagInputs();
  });
})();
