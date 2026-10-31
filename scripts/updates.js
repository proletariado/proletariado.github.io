$(document).ready(function() {
    // One data file per update source. To add another source later,
    // add its data file to this list. Missing or broken files are skipped.
    var UPDATE_SOURCES = [
        'data/steam_updates.json'
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
                // Lists are the current format; objects are the old format
                if (Array.isArray(data)) return data;
                return Object.values(data || {});
            })
            .catch(function(err) {
                console.error('Failed to load ' + path + ':', err);
                return [];
            });
    }

    function renderBuilds(data) {
        var section = document.getElementById('latestPatchesSection');
        var container = document.getElementById('latest-patches');

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
            img.src = entry.steamheader || '';
            img.alt = entry.title || 'Steam Build';
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
    }

    Promise.all(UPDATE_SOURCES.map(loadSource)).then(function(lists) {
        var merged = [].concat.apply([], lists);

        // Newest first across all sources. Entries without a timestamp sort last,
        // and ties keep their original order.
        merged.sort(function(a, b) {
            return (b.timestamp || 0) - (a.timestamp || 0);
        });

        renderBuilds(merged);
    });
});
