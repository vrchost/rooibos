/* pass any number of script URLs followed by one function to be called once scripts are loaded */
function load_scripts(srcs, func) {
    var f = (srcs.length > 1) ? function() { load_scripts(srcs.slice(1), func) } : func;
    var e = document.createElement("script");
    e.src = srcs[0];
    e.type = "text/javascript";
    e.onreadystatechange = f;
    e.onload = f;
    document.getElementsByTagName("head")[0].appendChild(e);
}
