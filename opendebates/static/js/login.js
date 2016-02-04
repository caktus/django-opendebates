(function() {
  var ODebates = window.ODebates || {};
  var login;
  ODebates.login = login = ODebates.login || {};

  login.init = function(callback) {
    // Maybe do some initial loading or variable setting here?


    // Call init handlers
    login.handlers.init();

    // do callback if exists, we can pass an object back here
    if (typeof callback === 'function') {
      var result = {
        sucess: true,
        errors: undefined
      };
      callback(result);
    }
  };

  login.handlers = {
    init: function() {
       
    }
  };
})();


