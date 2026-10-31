$(document).ready(function() {
    // One data file per wishlist source. To add another wishlist later,
    // add its data file to this list. Missing or broken files are skipped.
    var WISHLIST_SOURCES = [
        'data/steam_wishlist.json'
    ];

    function loadSource(path) {
        return fetch(path, {
                cache: "no-store"
            })
            .then(function(resp) {
                if (!resp.ok) throw new Error('Network response was not ok');
                return resp.json();
            })
            .then(function(data) {
                return Array.isArray(data) ? data : [];
            })
            .catch(function(err) {
                console.error('Failed to load ' + path + ':', err);
                return [];
            });
    }

    function renderWishlist(data) {
        var section = document.getElementById('wishlistSection');
        var container = document.getElementById('wishlist-tiles');

        if (!data || data.length === 0) {
            $(section).hide();
            return;
        }

        container.innerHTML = '';

        data.forEach(function(entry) {
            if (!entry || !entry.steamheader) return;

            var card = document.createElement('div');
            card.className = 'patch-entry';

            var img = document.createElement('img');
            img.src = entry.steamheader;
            img.alt = entry.name || 'Wishlist Game';
            card.appendChild(img);

            if (entry.date) {
                var overlay = document.createElement('div');
                overlay.className = 'patch-date-overlay';
                overlay.textContent = entry.date;
                card.appendChild(overlay);
            }

            var leftLink = document.createElement('a');
            leftLink.className = 'hover-zone left-zone';
            leftLink.href = entry.steamdburl || '#';
            leftLink.target = '_blank';
            leftLink.rel = 'noopener noreferrer';
            card.appendChild(leftLink);

            var rightLink = document.createElement('a');
            rightLink.className = 'hover-zone right-zone';
            rightLink.href = entry.rinurl || '#';
            rightLink.target = '_blank';
            rightLink.rel = 'noopener noreferrer';
            card.appendChild(rightLink);

            var leftText = document.createElement('div');
            leftText.className = 'hover-text left';
            leftText.textContent = 'Patch Notes';
            card.appendChild(leftText);

            var rightText = document.createElement('div');
            rightText.className = 'hover-text right';
            rightText.textContent = 'Download';
            card.appendChild(rightText);

            container.appendChild(card);
        });

        $(section).show();
    }

    Promise.all(WISHLIST_SOURCES.map(loadSource)).then(function(lists) {
        var merged = [].concat.apply([], lists);

        // Newest release first across all sources (ISO dates sort as strings)
        merged.sort(function(a, b) {
            return (b.released || '').localeCompare(a.released || '');
        });

        renderWishlist(merged);
    });
});
