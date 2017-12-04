% results_list, totalpages, pagenum = results
<ul class="sync-pagination pagination-sm"></ul>
% for item in results_list:
    % docid = item[0]
    % url = item[1]
    % title = item[2]
    % description = item[3]
    % rank = item[4]
    <div class="panel panel-default">
        <div class="panel-body">
            <a class='text-primary' href='{{url}}'><h4>{{title}}</h4></a>
            <small class='text-success'>{{url}}</small>
        </div>
    </div>
% end