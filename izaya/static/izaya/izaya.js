// Listeners live on the document, so widgets added to the page later need no setup.
(() => {
  "use strict";

  // An htmx partial can run this script again, which would double every listener.
  if (window.izayaLoaded) return;
  window.izayaLoaded = true;

  const part = (root, name) => root.querySelector(`[data-izaya-${name}]`);
  const options = (root) => [...part(root, "listbox").querySelectorAll("[data-izaya-key]")];
  const chips = (root) => [...part(root, "selection").querySelectorAll("[data-izaya-chip]")];
  const isOpen = (root) => !part(root, "listbox").hidden;
  const classNames = (value) => value.split(/\s+/).filter(Boolean);

  const chipKey = (chip) => chip.querySelector("input").value;
  const findChip = (root, key) => chips(root).find((chip) => chipKey(chip) === key);

  const notify = (root, name, detail) => {
    part(root, "live").textContent = detail.label;
    root.dispatchEvent(new CustomEvent(`izaya:${name}`, { bubbles: true, detail }));
  };

  const close = (root) => {
    const input = part(root, "input");
    const listbox = part(root, "listbox");
    listbox.hidden = true;
    listbox.style.display = "none";
    listbox.replaceChildren();
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  };

  const open = (root) => {
    const listbox = part(root, "listbox");
    listbox.hidden = false;
    listbox.style.display = "";
    part(root, "input").setAttribute("aria-expanded", "true");
  };

  const setActive = (root, active) => {
    for (const option of options(root)) {
      for (const name of classNames(root.dataset.izayaActiveClass)) {
        option.classList.toggle(name, option === active);
      }
    }
    part(root, "input").setAttribute("aria-activedescendant", active.id);
    active.scrollIntoView({ block: "nearest" });
  };

  // Removed rather than hidden, so screen readers don't announce a prompt for a filled field.
  const syncPlaceholder = (root) => {
    if ("izayaMultiple" in root.dataset) return;
    const input = part(root, "input");
    if (chips(root).length) {
      input.removeAttribute("placeholder");
    } else {
      input.placeholder = input.dataset.izayaPlaceholder ?? "";
    }
  };

  const removeChip = (root, chip) => {
    const detail = {
      key: chipKey(chip),
      label: part(chip, "chip-label").textContent,
    };
    chip.remove();
    syncPlaceholder(root);
    notify(root, "remove", detail);
  };

  const addChip = (root, key, label) => {
    const chip = part(root, "chip-template").content.firstElementChild.cloneNode(true);
    chip.querySelector("input").value = key;
    part(chip, "chip-label").textContent = label;
    part(root, "selection").append(chip);
    syncPlaceholder(root);
    notify(root, "select", { key, label });
  };

  const select = (root, option) => {
    const { izayaKey: key, izayaLabel: label } = option.dataset;
    const existing = findChip(root, key);
    if (existing) {
      if ("izayaMultiple" in root.dataset) removeChip(root, existing);
    } else {
      if (!("izayaMultiple" in root.dataset)) chips(root).forEach((chip) => removeChip(root, chip));
      addChip(root, key, label);
    }
    const input = part(root, "input");
    input.value = "";
    close(root);
    input.focus();
  };

  const prepareOptions = (root) => {
    const listbox = part(root, "listbox");
    const { izayaOptionClass, izayaMessageClass } = root.dataset;
    options(root).forEach((option, index) => {
      option.id = `${listbox.id}_${index}`;
      option.classList.add(...classNames(izayaOptionClass));
      option.setAttribute("aria-selected", String(Boolean(findChip(root, option.dataset.izayaKey))));
    });
    const message = part(listbox, "message");
    if (message) {
      message.classList.add(...classNames(izayaMessageClass));
      part(root, "live").textContent = message.textContent;
    }
  };

  // htmx drops error responses, but a denied search carries a message for the user.
  document.addEventListener("htmx:beforeSwap", (event) => {
    if (event.detail.xhr.status !== 403) return;
    if (!event.detail.target.matches("[data-izaya-listbox]")) return;
    event.detail.shouldSwap = true;
    event.detail.isError = false;
  });

  document.addEventListener("htmx:afterSwap", (event) => {
    const listbox = event.detail.target;
    if (!listbox.matches("[data-izaya-listbox]")) return;
    const root = listbox.closest("[data-izaya]");
    const input = part(root, "input");
    // A response can land after the user has already picked something or moved on.
    if (document.activeElement !== input || !input.value.trim() || !listbox.children.length) {
      close(root);
      return;
    }
    prepareOptions(root);
    input.removeAttribute("aria-activedescendant");
    open(root);
  });

  document.addEventListener("keydown", (event) => {
    if (!event.target.matches("[data-izaya-input]")) return;
    const root = event.target.closest("[data-izaya]");
    const all = options(root);
    const index = all.findIndex((option) => option.id === event.target.getAttribute("aria-activedescendant"));

    const canRemove = !event.repeat && !event.target.readOnly && !event.target.value;
    if (event.key === "Backspace" && canRemove && chips(root).length) {
      removeChip(root, chips(root).at(-1));
    } else if (event.key === "Escape" && isOpen(root)) {
      event.preventDefault();
      close(root);
    } else if (event.key === "Enter" && isOpen(root) && all[index]) {
      event.preventDefault();
      select(root, all[index]);
    } else if ((event.key === "ArrowDown" || event.key === "ArrowUp") && isOpen(root) && all.length) {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      const start = index === -1 && step === -1 ? 0 : index;
      setActive(root, all[(start + step + all.length) % all.length]);
    }
  });

  // Keep focus in the input while clicking or scrolling the results.
  document.addEventListener("mousedown", (event) => {
    if (event.target.closest("[data-izaya-listbox]")) event.preventDefault();
  });

  document.addEventListener("click", (event) => {
    const root = event.target.closest("[data-izaya]");
    if (!root) return;
    const option = event.target.closest("[data-izaya-key]");
    const remove = event.target.closest("[data-izaya-remove]");
    if (option) {
      select(root, option);
    } else if (remove) {
      removeChip(root, remove.closest("[data-izaya-chip]"));
      part(root, "input").focus();
    }
  });

  document.addEventListener("focusout", (event) => {
    const root = event.target.closest("[data-izaya]");
    if (root && !root.contains(event.relatedTarget)) close(root);
  });
})();
