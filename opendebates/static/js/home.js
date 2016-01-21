(function() {
  var ODebates = window.ODebates || {};
  var home;
  ODebates.home = home = ODebates.home || {};

  home.init = function(callback) {
    // Maybe do some initial loading or variable setting here?


    // Call init handlers
    home.handlers.init();

    // do callback if exists, we can pass an object back here
    if (typeof callback === 'function') {
      var result = {
        sucess: true,
        errors: undefined
      };
      callback(result);
    }
  };

  home.handlers = {
    init: function() {
      $('.glyphicon-trash').off('click');
      $('.glyphicon-trash').on('click', function(event) {
        var context = {
          title: 'Message Title',
          confirm: 'Ok!',
          body: 'Hey I\'m a message!'
        };
        var modalHtml = Handlebars.templates['modal'](context);

        $('body').append(modalHtml);
        $('.modal').modal();
        
      });
    }
  };
})();


