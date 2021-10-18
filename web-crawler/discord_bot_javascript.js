var world_name = "";

function findNodeByXPath(path, keyword) {
    var evaluator = new XPathEvaluator(),
        pattern =
            path +
            `[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ-', 'abcdefghijklmnopqrstuvwxyz-'),'` +
            keyword +
            `')]`;

    return evaluator.evaluate(
        pattern,
        document.documentElement,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
    );
}

var result = findNodeByXPath("//strong", world_name.toLowerCase());
var content;
if (result.singleNodeValue) {
    server_infos =
        result.singleNodeValue.parentNode.parentNode.innerText.split(`\t`);
    server_location = server_infos[3];
    timezone = findNodeByXPath("//strong", server_location.toLowerCase());
    now_time =
        timezone.singleNodeValue.parentNode.lastElementChild.innerText.split(
            ", "
        )[1];
    server_infos.push(now_time);

    content = server_infos.join(",");
} else {
    content = "empty";
}
