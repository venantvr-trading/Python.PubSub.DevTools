function filterEvents() {
    const filter = document.getElementById('event-filter').value.toLowerCase();
    const events = document.querySelectorAll('.timeline-event');

    events.forEach(event => {
        const eventName = event.getAttribute('data-event-name').toLowerCase();
        if (eventName.includes(filter)) {
            event.style.display = 'block';
        } else {
            event.style.display = 'none';
        }
    });
}
