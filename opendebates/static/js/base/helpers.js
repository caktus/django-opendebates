(function() {
  var ODebates = window.ODebates || {};
  var grecaptcha = window.grecaptcha;
  ODebates.helpers = ODebates.helpers || {};

  ODebates.helpers.getParameterByName = function(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? null : decodeURIComponent(results[1].replace(/\+/g, " "));
  };

  ODebates.helpers.strTrim = function (str) {
    if (typeof str === "string") {
      return str.replace(/^\s\s*/, '').replace(/\s\s*$/, '');
    }
  };

  ODebates.helpers.isValidDate = function (d) {
    if ( Object.prototype.toString.call(d) !== "[object Date]" ){
      return false;
    }
    return !isNaN(d.getTime());
  };

  ODebates.helpers.isNumber = function (n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
  };

  ODebates.helpers.capitalizeFirst = function (string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  };

  ODebates.helpers.calcPercent = function(count, total) {
    return (ODebates.helpers.isNumber(count) &&
           ODebates.helpers.isNumber(total) &&
           count > 0 &&
           total > 0) ?
           (count / total) * 100 : undefined;
  };

  ODebates.helpers.sign = function (x) {
    return typeof x === 'number' ? x ? x < 0 ? -1 : 1 : x === x ? 0 : NaN : NaN;
  };

  ODebates.helpers.validateEmail = function(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
  };

  ODebates.helpers.castVote = function(voterData, voteUrl, callback) {
    var data = JSON.parse(JSON.stringify(voterData));
    data.csrfmiddlewaretoken = $("[name=csrfmiddlewaretoken]").val();
    $.post(voteUrl, data, function(resp) {
      if (resp.status === "200") {
        $(".big-idea[data-idea-id="+resp.id+"]").find(".vote-tally-number").html(resp.tally);
        $(".big-idea[data-idea-id="+resp.id+"]").find(".vote-button").hide();
        $(".big-idea[data-idea-id="+resp.id+"]").find(".already-voted-button").css("display", "block");

      } else {
        $.each(resp.errors, function(key, vals) {
          if (key === 'captcha') {
            $('#captcha-help-block').html(vals.join(' '));
          } else {
            $('#modal-vote').find(':input[name='+key+']')
              .closest('.controls')
              .find('.help-block')
              .html(vals.join(' '));
          }
        });
        /* Reset captcha if the form had errors, because we can only
           validate a captcha token once, so we'll need a new one for
           the next time they submit. */
        grecaptcha.reset();
      }
      if (typeof callback === 'function') {
        callback(resp);
      }
    });
  };

  $("#sidebar_question_btn").on("click", function() {
    $(this).hide();
    $('#add_question_form_well').slideDown();
    return false;
  });

  $(".search-only form .input-group-addon").on("click", function () {
    $(this).closest("form").submit();
  });

  if (ODebates.voter && ! ODebates.vote_needs_captcha) {
    /* If the modal is activated but we already know the voter and
       don't need a captcha, don't activate the modal; just submit a vote. */
    $(".modal-vote").on("show.bs.modal", function (e) {
      e.preventDefault();
      ODebates.helpers.castVote({"email": ODebates.voter.email, "zipcode": ODebates.voter.zip},
          $(e.relatedTarget).data("vote-url"));
    });
  }
  if (ODebates.voter) {
    $(window).load(function() {
      try {
        ODebates.votesCast = JSON.parse($("#my-votes-cast").text());
      } catch(e) {
        ODebates.votesCast = {};
      }
      $.each(ODebates.votesCast.submissions || [], function(i, objId) {
        var idea = $(".big-idea[data-idea-id="+objId+"]");
        if (!idea) { return; }
        idea.find(".vote-button").hide();
        idea.find(".already-voted-button").css("display", "block");
      });
    });
  }

  $(".vote-button").on("click", function () {
    /* vote-button is the 'VOTE!' button under the vote count displayed on each idea */
    $($(this).data("target")).find("[data-vote-url]").attr("data-vote-url", $(this).data("vote-url"));
  });

  $(".votebutton").on("click", function () {
    /* .votebutton is the "submit" button in the modal vote dialog */
    var that = this,
        $form = $(this).closest('form');
    $form.find(".vote-error").addClass("hidden");
    var data = {
      "email": $form.find(":input[name=email]").val(),
      "zipcode": $form.find(":input[name=zipcode]").val()
    };
    if (ODebates.vote_needs_captcha) {
      data["g-recaptcha-response"] = $form.find(":input[name=g-recaptcha-response]").val();
    }
    ODebates.helpers.castVote(data, $(this).data("vote-url"), function(resp) {
      if (resp.status === "200") {
        $(that).closest(".modal").modal("hide");
        if (!ODebates.voter) {
          window.location.reload();
        }
      }
    });
    return false;
  });

  // adapted from http://codepen.io/lucien144/blog/highlight-asterix-in-placeholder-w-different-color
  if (RegExp(' AppleWebKit/').test(navigator.userAgent)) {
    $('input.required').each(function() {
      if (RegExp(/^\*/).test($(this).attr('placeholder'))) {
        return $(this).attr('placeholder', $(this).attr('placeholder').replace('*', ''));
      }
    });
  }

  $(window).load(function() {

    // Break vote count into spans for styling
    $(".header-votes .number").each(function(){
      var $el = $(this);
      var text = $el.text();
      $el.html("");
      for (var i=0; i<text.length; i++) {
        $el.append("<span><span>"+text[i]+"</span></span>");
      }
    });

    var src = ODebates.helpers.getParameterByName("source");
    if (typeof src === "string") {
      $.cookie("opendebates.source", src, { path: "/" });
    }

    if (typeof ODebates.stashedSubmission !== 'undefined') {
      var form = $("#add_question form");
      form.find(":input[name=category]").val(ODebates.stashedSubmission.category);
      form.find(":input[name=question]").val(ODebates.stashedSubmission.question);
      form.find(":input[name=citation]").val(ODebates.stashedSubmission.citation || '');
      form.submit();
    }

    if ($("#recent-activity").length === 1) {
      var fetch = function(delay) {
        $.get("/recent/")
            .done(function (data) {
              /* If successful, update page */
              $("#recent-activity").html(data);
            })
            .always(function () {
              /* Wait a little longer each time */
              delay = delay + 2000;
              setTimeout(fetch, delay, delay);
            });
      };
      /* Run first time immediately, to fill in that part of the page */
      setTimeout(fetch, 0, 0);
    }
  });

})();
