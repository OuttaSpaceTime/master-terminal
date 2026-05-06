# Custom rdbg command helpers loaded by debug.gem at startup.

require 'json'
module RdbgClaudePrompt
  MAX_SOURCE_LINES = 15
  MAX_LOCALS = 20
  MAX_PREVIEW_LENGTH = 700

  class << self
    def register!
      return unless defined?(DEBUGGER__::SESSION)

      DEBUGGER__::SESSION.send(:register_command, 'claude', 'prompt', unsafe: false) do |arg|
        ask(arg)
        :retry
      end
    rescue StandardError => err
      warn "rdbg claude command setup failed: #{err.class}: #{err.message}"
    end

    def ask(arg)
      question = arg.to_s.strip
      question = 'What should I inspect next? Suggest the most useful rdbg commands.' if question.empty?

      payload = {
        question: question,
        reasoning: 'm',
        debugger_context: render_context,
        metadata: metadata
      }

      stdout, status = run_helper(JSON.generate(payload))

      unless status.success?
        details = stdout.strip
        details = 'no output from helper script' if details.empty?
        puts "claude prompt failed (#{status.exitstatus}): #{details}"
        return
      end

      puts stdout.strip
    rescue SystemCallError => err
      puts "claude prompt failed: #{err.class}: #{err.message}"
    end

    def render_context
      tc = DEBUGGER__::ThreadClient.current
      frame = tc.current_frame

      sections = []
      sections << render_frame(frame)
      sections << render_source(frame)
      sections << render_locals(tc, frame)
      sections << render_backtrace(tc)
      sections.compact.join("\n\n")
    rescue StandardError => err
      "Could not capture rdbg context: #{err.class}: #{err.message}"
    end

    def render_frame(frame)
      return 'Current frame: unavailable' unless frame

      [
        'Current frame:',
        "name: #{frame.name}",
        "location: #{frame.location_str}",
        "self: #{preview(frame.self)}"
      ].join("\n")
    end

    def render_source(frame)
      return unless frame&.path && frame.location
      return unless File.file?(frame.path)

      line = frame.location.lineno
      start_line = [line - (MAX_SOURCE_LINES / 2), 1].max
      end_line = line + (MAX_SOURCE_LINES / 2)

      lines = File.readlines(frame.path, chomp: true)
      body = (start_line..[end_line, lines.length].min).map do |lineno|
        marker = lineno == line ? '=>' : '  '
        "#{marker} #{lineno}: #{lines[lineno - 1]}"
      end

      (["Source around current line:"] + body).join("\n")
    rescue StandardError => err
      "Source around current line: unavailable (#{err.class}: #{err.message})"
    end

    def render_locals(tc, frame)
      return 'Locals: unavailable' unless frame

      locals = tc.collect_locals(frame).first(MAX_LOCALS).map do |name, value|
        "#{name}: #{preview(value)}"
      end

      return 'Locals: none' if locals.empty?

      (["Locals:"] + locals).join("\n")
    rescue StandardError => err
      "Locals: unavailable (#{err.class}: #{err.message})"
    end

    def render_backtrace(tc)
      frames = tc.instance_variable_get(:@target_frames)
      return 'Backtrace: unavailable' unless frames

      body = frames.first(8).each_with_index.map do |frame, index|
        "#{index}: #{frame.name} at #{frame.location_str}"
      end

      (["Backtrace:"] + body).join("\n")
    rescue StandardError => err
      "Backtrace: unavailable (#{err.class}: #{err.message})"
    end

    def metadata
      {
        ruby_version: RUBY_VERSION,
        debug_version: Gem.loaded_specs['debug']&.version&.to_s,
        rails_env: (Rails.env if defined?(Rails) && Rails.respond_to?(:env)),
        pwd: Dir.pwd
      }.compact
    end

    def preview(value)
      text = DEBUGGER__.safe_inspect(value, short: true)
      text.length > MAX_PREVIEW_LENGTH ? "#{text[0, MAX_PREVIEW_LENGTH]}..." : text
    end

    def helper_env
      env = { 'RUBY_DEBUG_ENABLE' => '0', 'RUBY_DEBUG_ADDED_RUBYOPT' => nil }
      rubyopt = ENV['RUBYOPT'].to_s
      added = ENV['RUBY_DEBUG_ADDED_RUBYOPT'].to_s

      if !rubyopt.empty? && !added.empty?
        env['RUBYOPT'] = rubyopt.split.reject { |entry| entry == added }.join(' ')
      end

      env
    end

    def run_helper(stdin_data)
      output = IO.popen(
        [helper_env, File.expand_path('~/.local/bin/rdbg-agent-prompt')],
        'r+',
        err: [:child, :out]
      ) do |io|
        io.write(stdin_data)
        io.close_write
        io.read
      end

      [output, $?]
    end
  end
end

RdbgClaudePrompt.register!
