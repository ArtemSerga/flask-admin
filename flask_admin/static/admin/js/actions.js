var AdminModelActions = function(actionErrorMessage, actionConfirmations) {
    // Actions helpers. TODO: Move to separate file
    this.execute = function(name) {
        var selected = $('input.action-checkbox:checked').size();

        if (selected === 0) {
            alert(actionErrorMessage);
            return false;
        }

        var msg = actionConfirmations[name];

        if (!!msg)
            if (!confirm(msg))
                return false;

        // Update hidden form and submit it
        var form = $('.form-horizontal');
        $('#action', form).val(name);

        form.submit();

        return false;
    };

    $(function() {
        $('.action-rowtoggle').change(function() {
            $('input.action-checkbox').attr('checked', this.checked);
        });
    });
};
