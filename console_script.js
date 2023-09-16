(async function() {
    let bookmarks = new Set();
    let lastScrollHeight = 0;
    let noNewBookmarksCount = 0;

    // Function to generate a random delay between two values (both inclusive)
    function randomDelay(min, max) {
        return Math.random() * (max - min) + min;
    }

    // Function to delay execution for a random duration between min and max
    function delay(min, max) {
        return new Promise(resolve => setTimeout(resolve, randomDelay(min, max)));
    }

    while (noNewBookmarksCount < 3) {  // Stop if no new bookmarks are loaded for 3 consecutive checks
        window.scrollTo(0, document.body.scrollHeight);
        
        await delay(3000, 6000);  // Wait for a random duration between 3 and 6 seconds
        
        let links = document.querySelectorAll('a[href*="/status/"]');
        let currentSize = bookmarks.size;

        links.forEach(link => {
            let url = `https://twitter.com${link.getAttribute('href')}`;
            if (!bookmarks.has(url) && !url.includes("/analytics")) {
                bookmarks.add(url);
            }
        });

        if (bookmarks.size === currentSize) {
            noNewBookmarksCount++;
        } else {
            noNewBookmarksCount = 0;
        }

        if (document.body.scrollHeight === lastScrollHeight) {
            break;
        }
        lastScrollHeight = document.body.scrollHeight;
        
        await delay(3000, 6000);  // Wait for a random duration between 3 and 6 seconds before the next scroll
    }

    // Convert bookmarks set to an array
    let bookmarkArray = Array.from(bookmarks);

    // Get the current date and time and format it for the filename
    let date = new Date();
    let formattedDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}_${String(date.getHours()).padStart(2, '0')}-${String(date.getMinutes()).padStart(2, '0')}-${String(date.getSeconds()).padStart(2, '0')}`;

    // Create a downloadable link for a text file containing the tweet URLs
    let blob = new Blob([bookmarkArray.join('\n')], {type: 'text/plain'});
    let link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = `all_bookmarks_${formattedDate}.txt`;
    link.textContent = 'Download all bookmarks';
    document.body.appendChild(link);
    link.click();
})()
