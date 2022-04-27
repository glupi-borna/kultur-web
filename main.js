window.onload = main;
window.onpopstate = () => load_page(location.href, true, true);
let q = document.querySelector.bind(document);
let qa = document.querySelectorAll.bind(document);

const mouse = { x: 0, y: 0 };
const screen_size = { x: 0, y: 0 };
let close_context = () => undefined;

const actions = {
    theme: () => {
        localStorage.setItem("theme-alt", document.documentElement.classList.toggle("alt"));
    },
    language: (evt) => {
        let languages = Object.keys(translations);
        let btns = languages.map(l => {
            let btn = document.createElement("button");
            if (l == language) {
                btn.className = "current";
            }
            let def = translations[l];
            btn.textContent = `${def.$name} ${def.$icon}`;
            btn.onclick = () => {
                if (language != l) {
                    language = l;
                    translate();
                    window.dispatchEvent(new Event("translated"));
                }
                close_context();
            };
            return btn;
        });
        let div = document.createElement("div");
        div.className = "menu";
        div.append(...btns);
        open_context(div, evt.target);
    }
};

let language = navigator.language.split("-")[0];
const translations = {
    hr: {
        $icon: "🇭🇷",
        $name: "Hrvatski",
        home: "Početna",
        about: "O nama",
        projects: "Projekti",
        language: "Jezik",
        color: "Boja",
        404: "Tražena stranica ne postoji!"
    },
    en: {
        $icon: "🇬🇧",
        $name: "English",
        home: "Home",
        about: "About us",
        projects: "Projects",
        language: "Language",
        color: "Color",
        404: "The requested page does not exist!"
    }
};

function is_click_outside(el, evt) {
    if (el === evt.target) { return false; }
    if (el.contains(evt.target)) { return false; }
    return true;
}

function extract_anchor_pos(rect, anchor) {
    return {
        x: rect.left + rect.width * anchor.x,
        y: rect.top + rect.height * anchor.y
    };
}

function open_context(body, target, anchor) {
    if (anchor == undefined) {
        anchor = {x: 1, y: 1};
    }

    let old = q(".context");
    if (old) { close_context(); }

    let attached = true;
    let el = document.createElement("div");
    el.className = "context";
    el.append(body);

    let style = target ? getComputedStyle(target) : null;
    let offset = {
        top:    target ? parseFloat(style.paddingTop)    : 0,
        bottom: target ? parseFloat(style.paddingBottom) : 0,
        left:   target ? parseFloat(style.paddingLeft)   : 0,
        right:  target ? parseFloat(style.paddingRight)  : 0,
    };

    let update_pos = () => {
        let x = mouse.clientX;
        let y = mouse.clientY;
        if (target) {
            let r = target.getBoundingClientRect();
            let rect = {
                left: r.left + offset.left,
                top: r.top + offset.top,
                width: r.width - offset.right - offset.left,
                height: r.height - offset.top - offset.bottom,
            }
            let pos = extract_anchor_pos(rect, anchor);
            x = pos.x; y = pos.y;
        }
        let transx = x > screen_size.x*0.5 ? "-100%" : "0%";
        let transy = y > screen_size.y*0.5 ? "-100%" : "0%";
        el.style.transform = `translate(${transx}, ${transy})`;
        el.style.left = x + "px";
        el.style.top = y + "px";
    };

    update_pos();
    document.body.append(el);

    listen_until_false(window, "resize", () => {
        update_pos();
        return attached;
    });

    close_context = () => {
        el.remove();
        attached = false;
        close_context = () => undefined;
    };

    setTimeout(
        ()=>listen_until_false(document.body, "click", (evt) => {
            if (!attached) { return false; }
            if (is_click_outside(el, evt)) {
                close_context();
                return false;
            }
            return true;
        })
    );
}

function listen_until_false(el, evt, cb) {
    let wrapped; wrapped = (...args) => {
        if (!cb(...args)) {
            el.removeEventListener(evt, wrapped);
        };
    }
    el.addEventListener(evt, wrapped);
}

async function load_page_text(href) {
    try {
        let page = await fetch(href);
        let page_text = await page.text();
        let main_text = page_text.match(/<main>([\w\W]+?)<\/main>/)[1];
        return main_text;
    } catch {
        return `
            <p trans=404>Tražena stranica ne postoji!</p>
        `;
    }
}

async function load_latest() {
    let main = q("main");
    if (!main) { throw new Error("Main is missing!"); }
    let text = await load_page_text(`posts/latest-${language}.html`);
    main.innerHTML = text;
    main.href = `posts/latest-${language}.html`;
    prepare_links();
    prepare_actions();
    translate();
}

window.addEventListener("translated", () => {
    if (location.href.endsWith("/index.html")) { load_latest(); }
});

const load_overrides = {
    "/index.html": load_latest
};

async function load_page(href, no_push, force) {
    if (href == location && !force) { return; }

    let overrides = Object.keys(load_overrides);
    for (let override of overrides) {
        if (href.endsWith(override)) {
            if (!no_push) { history.pushState(null, "", href); }
            return load_overrides[override]();
        }
    }

    let main = q("main");
    if (!main) { throw new Error("Missing main!"); }

    let text = await load_page_text(href);
    main.innerHTML = text;
    if (!no_push) { history.pushState(null, "", href); }
    prepare_links();
    prepare_actions();
    translate();
}

function translation_get(key) {
    let map = translations[language] || translations.hr;
    return map[key];
}

function translate(els) {
    if (els == undefined) {
        els = qa("[trans]");
    }

    for (let el of els) {
        el.innerText = translation_get(el.attributes.trans.value) || el.innerText;
    }
}

function prepare_actions() {
    let els = qa("[action]");
    for (let el of els) {
        el.onclick = actions[el.attributes.action.value];
    }
}

function prepare_links() {
    let links = [...qa("a[href]"), ...qa("a[old-href]")];
    for (let link of links) {
        let href = link.href;
        if (href == "") { href = link.getAttribute("old-href"); }
        if (location == href) {
            link.classList.add("current");
        } else {
            link.classList.remove("current");
        }

        link.removeAttribute("href");
        link.setAttribute("old-href", href);
        link.onclick = () => { load_page(href); };
    }
}

function update_mouse(evt) {
    mouse.x = evt.clientX;
    mouse.y = evt.clientY;
}

function update_screen() {
    screen_size.x = window.innerWidth;
    screen_size.y = window.innerHeight;
}

function load_theme() {
    let alt = JSON.parse(localStorage.getItem("theme-alt") || "false");
    if (alt) { document.documentElement.classList.toggle("alt", alt); }
}

function main() {
    document.body.onmousemove = update_mouse;
    document.body.onresize = update_screen;
    load_theme();
    update_screen();
    prepare_links();
    prepare_actions();
    translate();
}