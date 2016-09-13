(function() {
  $(window).load(function() {
    $(".form-group").each(function() {
      var $label = $(this).find("label");
      if ($label.length === 1) {
        var text = $label.text();

        if ($label.hasClass("required")) {
          text = "* " + text;
        }

        // Take any prefixing text out of the label, and put it in
        // the placeholder instead.  Any HTML content that exists
        // after the label's text content gets to stay in the label.
        $(this).find("input").attr("placeholder", text);
        $label.html($label.html().replace($label.text(), ''));
      }
    });
  });
})();
