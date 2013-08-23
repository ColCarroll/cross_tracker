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

function disable_other(elem) {
      var otherfields = elem.closest(".resultfields").find(".resultfield").not(elem).not(".fileupload-exists");
      var button = elem.closest("form").find(":submit");
      if (elem.val().length || elem.find(".fileupload-preview").text().length) {
        otherfields.attr("disabled", "disabled");
        button.removeAttr("disabled");
      } else {
        otherfields.removeAttr("disabled");
        button.prop("disabled",true);
      }
}

$(document).ready(function () {
  $(".resultfields").find(".resultfield").each(function () {
    var elem = $(this);
# disable_other(elem);
    elem.on("propertychange keyup input paste change", function (event) {
#     disable_other(elem);
    });
  });
});
