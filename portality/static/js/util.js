$.extend(true, doaj, {
    util: {
        clickToCopy: () => {
            const copyBtn = `
            <button type="button" class="click-to-copy" aria-label="Copy value to clipboard">
                <i data-feather="copy" aria-hidden="true"></i>
                <span class="click-to-copy--confirmation" style="display: none;">Value copied!</span>
            </button>
        `;

            const onClick = function (event, $valueElem) {
                if (!$valueElem.length) return;
                const textToCopy = $valueElem.val() || $valueElem.text();
                const $btn = $(event.currentTarget);
                const $msg = $btn.find('.click-to-copy--confirmation');

                navigator.clipboard.writeText(textToCopy)
                    .then(() => {
                        $msg.text('Value copied!').show();
                        setTimeout(() => $msg.hide(), 3000);
                    })
                    .catch(err => console.error('Failed to copy:', err));
            };

            $("[data-widget--click-to-copy]").each(function () {
                const $element = $(this);
                const $copyBtn = $(copyBtn);
                $copyBtn[0].id = $element[0].id + '-copy';
                $copyBtn.attr('data-copy-target', $element[0].id);
                $copyBtn.attr('aria-label', `Copy "${$element.val() || $element.text()}" to clipboard`);
                $copyBtn.data('copyTarget', $element);
                $element.after($copyBtn);
                $copyBtn.on("click", (event) => onClick(event, $element));
            });

        }
    }
});

doaj.util.clickToCopy();