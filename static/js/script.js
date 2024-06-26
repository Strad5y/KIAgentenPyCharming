document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.querySelector('[data-collapse-toggle="mobile-menu"]');
    const menu = document.querySelector('#mobile-menu');
    toggleButton.addEventListener('click', () => {
        if (menu.classList.contains('hidden')) {
            menu.classList.remove('hidden');
        } else {
            menu.classList.add('hidden');
        }
    });

    const proceedButton = document.getElementById('proceed-button');
    const landingPage = document.getElementById('landing-page');
    const mainInterface = document.getElementById('main-interface');

    proceedButton.addEventListener('click', () => {
        landingPage.classList.add('hidden');
        mainInterface.classList.remove('hidden');
    });
});
