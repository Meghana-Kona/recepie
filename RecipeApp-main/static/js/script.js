document.getElementById("choiceSearch").addEventListener("input", function() {
  let val = this.value;
  fetch("/search_choice?q=" + val)
    .then(res => res.json())
    .then(data => {
      let output = "";
      data.forEach(item => output += "<p>" + item + "</p>");
      document.getElementById("choiceSuggestions").innerHTML = output;
    });
});
