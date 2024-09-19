function enableTooltip(tooltipIconId, tooltipTextId) {
    const tooltipIcon = document.getElementById(tooltipIconId);
    const tooltipText = tooltipIcon.querySelector('.tooltip');

    tooltipIcon.addEventListener('mouseenter', function () {
        tooltipText.classList.add('tooltip-visible');
    });

    tooltipIcon.addEventListener('mouseleave', function () {
        tooltipText.classList.remove('tooltip-visible');
    });
}

enableTooltip('tooltipIcon1');
enableTooltip('tooltipIcon2');
enableTooltip('tooltipIcon3');