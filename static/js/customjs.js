jQuery(function($) {

    $('form[data-async]').on('submit', function(event) {
        var $form = $(this);
        var $target = $($form.attr('data-target'));
 
        $.ajax({
            type: $form.attr('method'),
            url: $form.attr('action'),
            data: $form.serialize(),
 
            success: function(data, status) {
                $target.html(data);
            }
        });
 
        event.preventDefault();
    });
});

$(document).ready(function () {
  $(".resultfields").find(".resultfield").each(function () {
    var elem = $(this);
    elem.bind("propertychange keyup input paste", function (event) {
      var otherfields = elem.closest(".resultfields").find(".resultfield").not($(this));
      var button = elem.closest("form").find(":submit");
      if (elem.val().length) {
        otherfields.attr("disabled", "disabled");
        button.removeAttr("disabled");
      } else {
        otherfields.removeAttr("disabled");
        button.prop("disabled",true);
      }
    });
  });
});
