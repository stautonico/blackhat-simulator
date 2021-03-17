let index = 0;
let error_title = document.getElementById("error-title");
let description_line = document.getElementById("description-line");
let link_line = document.getElementById("link-line");
const SPEED = 50;


const text = {
    "403": {
        "description": "You are not allowed to view this page",
        "links": `You could try <a href="${document.referrer}">going back</a> or <a href="/">going home</a>`
    },
    "404": {
        "description": "The page you are looking for might have been removed, had its name changed or is temporarily unavailable",
        "links": `You could try <a href="${document.referrer}">going back</a> or <a href="/">going home</a>`
    },
    "404brain": {
        "description": "Steve's \"big brain\" that he keeps talking about couldn't be found (probably because it doesn't exist)",
        "links": "You might find his \"big brain\" <a href=\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\">here</a>"
    }
}


let currentLine = "description";
let done = false;

function write_title(error) {
    let errorTitle = (error === "404brain") ? "404" : error;
    if (!done) {

        let title = `Error <span class="errorcode">${errorTitle}</span>`
        if (index <= title.length) {
            // Try to skip html tags
            if (title[index] === "<") {
                // Find the matching >
                let currentChar = title[index];
                let counter = index;
                while (currentChar !== ">") {
                    counter++;
                    currentChar = title[counter];
                }

                error_title.innerHTML = title.substr(0, counter) + "_";
                index = counter;
            } else {
                error_title.innerHTML = title.substr(0, index++) + "_";
            }
            setTimeout(() => {write_title(error);}, SPEED)
        } else {
            index = 0;
            error_title.innerHTML = title;
            description_line.classList.toggle("hidden");
            description_line.innerText = "";
            link_line.innerText = "";
            done = true;
            setTimeout(() => {write_title(error);}, SPEED)
        }
    } else {
        next_letter(error);
    }
}

function next_letter(error) {
    if (currentLine === "description") {
        if (index <= text[error].description.length) {
            // Try to skip html tags
            if (text[error].description[index] === "<") {
                // Find the matching >
                let currentChar = text[error].description[index];
                let counter = index;
                while (currentChar !== ">") {
                    counter++;
                    currentChar = text[error].description[counter];
                }

                description_line.innerHTML = text[error].description.substr(0, counter) + "_";
                index = counter;
            } else {
                description_line.innerHTML = text[error].description.substr(0, index++) + "_";
            }
            setTimeout(() => {next_letter(error);}, SPEED)
        } else {
            currentLine = "link";
            index = 0;
            description_line.innerHTML = text[error].description;
            link_line.classList.toggle("hidden");
            setTimeout(() => {next_letter(error);}, SPEED)
        }
    } else {
        if (index <= text[error].links.length) {
            // Try to skip html tags
            if (text[error].links[index] === "<") {
                // Find the matching >
                let currentChar = text[error].links[index];
                let counter = index;
                while (currentChar !== ">") {
                    counter++;
                    currentChar = text[error].links[counter];
                }

                link_line.innerHTML = text[error].links.substr(0, counter) + "_";
                index = counter;
            } else {
                link_line.innerHTML = text[error].links.substr(0, index++) + "_";
            }
                setTimeout(() => {next_letter(error);}, SPEED)
        } else {

            link_line.innerHTML = text[error].links;
            setInterval(() => {
                link_line.classList.toggle("blink-cursor");
            }, 500);
        }
    }
}

function main(error) {
    error_title.innerText = "";
    error_title.classList.toggle("hidden");
    write_title(error);
}