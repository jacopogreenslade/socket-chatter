function loadJsFileHeader(path) {
    var head = document.getElementsByTagName('head')[0];
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = path;
    head.appendChild(script);
}

function loadApp() {
  console.log("Initializing app")
  for (const path of directories) {
    loadJsFileHeader(path);
  }
  // Don't really like this but the app isn't ready
  // immediately. We need to wait a second to start
  window.setTimeout(() => {
    // The anonymous function actually stops this from
    // failing because it runs AFTER the function is loaded
    initApp(); 
  }, 1000);
}

const directories = [
  "src/app.js", 
  "src/dom.js", 
  "src/model.js",
];

window.onload = loadApp();