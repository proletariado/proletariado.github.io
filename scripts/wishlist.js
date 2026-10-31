$(document).ready(function() {
    function renderWishlist(data) {
        var section = document.getElementById('wishlistSection');
        var container = document.getElementById('wishlist-tiles');

        if (!Array.isArray(data) || data.length === 0) {
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
            leftText.textContent = 'SteamDB';
            card.appendChild(leftText);

            var rightText = document.createElement('div');
            rightText.className = 'hover-text right';
            rightText.textContent = 'Download';
            card.appendChild(rightText);

            container.appendChild(card);
        });

        $(section).show();
    }

    fetch('data/wishlist.json', {
            cache: "no-store"
        })
        .then(function(resp) {
            if (!resp.ok) throw new Error('Network response was not ok');
            return resp.json();
        })
        .then(renderWishlist)
        .catch(function(err) {
            console.error('Failed to load wishlist info:', err);
        });
});
