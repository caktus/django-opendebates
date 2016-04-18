(function() {
  $(window).load(function() {
    $(".form-group").each(function() {
      if ($(this).find("label").length === 1) {
        var text = $(this).find("label").hide().text();

        if ($(this).find("label").hasClass("required")) {
          text = "* " + text;
        }

        $(this).find("input").attr("placeholder", text);
      }
    });
  });
})();
