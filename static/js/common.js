function enableTooltips() {
    const tooltipIcons = document.querySelectorAll('.has-tooltip');  // Select all elements with the 'has-tooltip' class

    tooltipIcons.forEach(tooltipIcon => {
        const tooltipText = tooltipIcon.querySelector('.tooltip');

        tooltipIcon.addEventListener('mouseenter', function () {
            tooltipText.classList.add('tooltip-visible');
        });

        tooltipIcon.addEventListener('mouseleave', function () {
            tooltipText.classList.remove('tooltip-visible');
        });
    });
}

enableTooltips();