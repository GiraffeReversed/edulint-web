
// based on https://github.com/plausible/analytics/discussions/482
var script = document.createElement('script');
// script.async = true;
script.defer = true;
script.src = "https://plaus.borysek.eu/plaus/js/script.js";
script.setAttribute("data-domain", window.location.host);
script.setAttribute("data-api", "https://plaus.borysek.eu/plaus/api/event");
document.head.append(script);
