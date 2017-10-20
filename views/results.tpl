% include('header.tpl', title=search_query + ' - Comet',userData = userData)

<div class="container-fluid">
    <div class='row'>
        <div class="col-md-8 col-sm-8 col-xs-10 col-md-offset-2 col-sm-offset-2 col-xs-offset-1">
            <div class="well">
                <p class="text-left">Your search query was:
                % if defined('search_query'):
                    <blockquote>
                    {{search_query}}
                    </blockquote></p>
                % end
            </div>

            <h2 class="text-primary">Word Count</h2>
            <table class="table table-condensed text-center" id="results">
                <thead>
                <tr>
                    <th class="text-center">Word</th>
                    <th class="text-center">Count</th>
                </tr>
                </thead>

                <!-- Created table of keywords searched and the number of times they appeared -->
                <tbody>
                % for x in range(0,len(insertion_order_list)):
                    <tr>
                        <td>{{insertion_order_list[x]}}</td>
                        <td>{{calculated[insertion_order_list[x]]}}</td>
                        
                    </tr>
                % end
                </tbody>
            </table>
            <br>
            
            
            
            <!-- Creates table to display top 20 most searched words -->		
            % if bool(top_words):
                <h2 class="text-primary">Search History</h2>
                <table class="table table-condensed text-center" id="history">
                    <thead>
                    <tr>
                        <th class="text-center">#</th>
                        <th class="text-center">Word</th>
                        <th class="text-center">Frequency</th>
                    </tr>
                    </thead>
                    <tbody>
                    % for (id,(word, frequency)) in enumerate(top_words, start=1):
                        <tr>
                            <td>{{id}}</td>
                            <td>{{word}}</td>
                            <td>{{int(frequency)}}</td>
                        </tr>
                    % end
                    </tbody>
                </table>
            % end

            <!-- Creates table to display top 10 recent queries -->		
            % if bool(recent_queries):
                <h2 class="text-primary">Recent Searches</h2>
                <table class="table table-condensed text-center" id="history">
                    <thead>
                    <tr>
                        <th class="text-center">#</th>
                        <th class="text-center">Word</th>
                    </tr>
                    </thead>
                    <tbody>
                    % for (id,word) in enumerate(recent_queries, start=1):
                        <tr>
                            <td>{{id}}</td>
                            <td>{{word}}</td>
                        </tr>
                    % end
                    </tbody>
                </table>
            % end
        </div>
    </div>
</div>
% include('footer.tpl') 