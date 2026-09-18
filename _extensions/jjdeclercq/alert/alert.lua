return {
  ['alert'] = function(args, kwargs, meta)
    -- Parse the argument (alert name)
    local alertName = pandoc.utils.stringify(args[1])
    
    -- Fetch alerts_list from metadata
    local alerts_list = meta["alerts_list"]
    if not alerts_list then
      return pandoc.Str("Error: alerts_list not found in metadata.")
    end

    local alertData = alerts_list[alertName]
    if not alertData then
      return pandoc.Str("Error: Alert '" .. alertName .. "' not found.")
    end

    -- Basic alert fields
    local title        = pandoc.utils.stringify(alertData["title"] or "Untitled")
    local type         = pandoc.utils.stringify(alertData["type"] or "note")
    local content      = pandoc.utils.stringify(alertData["content"] or "No content provided.")
    local showIcon     = alertData["icon"] ~= false         -- icon defaults to true
    local collapsible  = alertData["collapse"] == true      -- collapse defaults to false

    -- New extra fields
    local date_created  = pandoc.utils.stringify(alertData["date_created"] or "")
    local resolved      = alertData["resolved"] == true     -- resolved must be true boolean
    local date_resolved = pandoc.utils.stringify(alertData["date_resolved"] or "")
    local resolution    = pandoc.utils.stringify(alertData["resolution"] or "")
    local include_extras = alertData["include_extras"] == true -- include_extras must be true boolean

    -- Build extra info (each item will be its own paragraph)
    local extra_info = {}
    if include_extras then
      if date_created ~= "" then
        table.insert(extra_info, "Date Created: " .. date_created)
      end
      if resolved then
        table.insert(extra_info, "Resolved: Yes")
        if date_resolved ~= "" then
          table.insert(extra_info, "Date Resolved: " .. date_resolved)
        end
        if resolution ~= "" then
          table.insert(extra_info, "Resolution: " .. resolution)
        end
      else
        table.insert(extra_info, "Resolved: No")
      end
    end

    -- Convert each extra info item into a separate paragraph block
    local extra_blocks = {}
    for _, item in ipairs(extra_info) do
      table.insert(extra_blocks, pandoc.Para({pandoc.Str(item)}))
    end

    -- Assemble the main content block followed by the extra info blocks
    local blocks = {}
    table.insert(blocks, pandoc.Para({pandoc.Str(content)}))
    for _, para in ipairs(extra_blocks) do
      table.insert(blocks, para)
    end

    -- Create the callout structure (title, type, content, etc.)
    local calloutDiv = {
      type = type,
      icon = showIcon,
      title = title,
      content = blocks,
      collapse = collapsible
    }

    -- Return the rendered callout via Quarto's Callout function
    return quarto.Callout(calloutDiv)
  end
}
